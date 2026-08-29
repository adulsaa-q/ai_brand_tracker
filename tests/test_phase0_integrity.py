"""Regression tests for Phase 0 integrity fixes."""

from __future__ import annotations

import os
import subprocess
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from src.analytics.metrics import MarketMetricsEngine
from src.analytics.opportunity import OpportunityFinder
from src.api import app
from src.brands import resolve_focal_brand
from src.engines._parsing import parse_brand_mentions
from src.engines.mock_engine import MockObservationEngine
from src.ids import new_observation_id

client = TestClient(app)


# --- 5.2 observation id integrity -------------------------------------------
def test_observation_ids_unique_under_rapid_creation():
    eng = MockObservationEngine()
    ids = {
        eng.observe(query_id=f"q{i}", query_text=f"query {i}", target_brands=["A", "B", "C"]).observation_id
        for i in range(500)
    }
    assert len(ids) == 500


def test_new_observation_id_unique():
    assert len({new_observation_id("gemini") for _ in range(10000)}) == 10000


# --- 5.3 provenance --------------------------------------------------------
def test_mock_provenance_is_honest():
    obs = MockObservationEngine().observe(query_id="q", query_text="ซื้อที่ไหนดี", target_brands=["A", "B"])
    assert obs.provider == "mock"
    assert obs.answer_surface == "synthetic"
    assert obs.grounding_enabled is False
    assert obs.response_raw_text.startswith("[SYNTHETIC]")


# --- 5.1 / structured output: parse status is explicit --------------------
def test_parse_status_transitions():
    ok_mentions, status = parse_brand_mentions(
        '```json\n{"brand_mentions":[{"brand_name":"Shopee","rank":1}]}\n```', query_id="q"
    )
    assert status == "ok" and len(ok_mentions) == 1

    _, status = parse_brand_mentions("no json here at all", query_id="q")
    assert status == "no_structured_output"

    _, status = parse_brand_mentions('```json\n{"brand_mentions": [ broken ]\n```', query_id="q")
    assert status == "parse_error"


# --- 5.4 focal brand identity -------------------------------------------------
_VERTICAL = {
    "focal_brand": "shopee",
    "brands": [
        {"id": "shopee", "name": "Shopee Thailand", "aliases": ["ช้อปปี้"], "is_focal_brand": True},
        {"id": "lazada", "name": "Lazada Thailand", "aliases": ["ลาซาด้า"]},
    ],
}


def test_resolve_focal_brand_maps_id_to_display_name():
    focal = resolve_focal_brand(_VERTICAL)
    assert focal.name == "Shopee Thailand"
    assert focal.matches("Shopee Thailand")
    assert focal.matches("shopee")
    assert focal.matches("ช้อปปี้")
    assert not focal.matches("Lazada Thailand")


def test_focal_leader_is_not_flagged_as_missed_opportunity():
    obs = [
        {
            "query_id": "q1",
            "query_text": "ซื้อสกินแคร์ที่ไหนดี",
            "category": "โปรโมชั่น",
            "brand_mentions": [
                {"brand_name": "Shopee Thailand", "rank": 1, "mentioned": True, "sentiment": "positive"},
                {"brand_name": "Lazada Thailand", "rank": 2, "mentioned": True, "sentiment": "neutral"},
            ],
        }
    ]
    metrics = MarketMetricsEngine.calculate_share_of_voice(obs)
    gaps = OpportunityFinder.identify_gaps(resolve_focal_brand(_VERTICAL), metrics, obs)
    # focal won rank 1 -> no CATEGORY gap, only the generic low-confidence note
    assert all(g.get("missed_query_count", 0) == 0 for g in gaps)
    assert gaps[0]["confidence"].startswith("LOW")


def test_focal_absent_is_flagged():
    obs = [
        {
            "query_text": "ซื้อสกินแคร์ที่ไหนดี",
            "category": "ความน่าเชื่อถือ",
            "brand_mentions": [{"brand_name": "Lazada Thailand", "rank": 1, "mentioned": True}],
        }
    ]
    gaps = OpportunityFinder.identify_gaps(resolve_focal_brand(_VERTICAL), {"brands": []}, obs)
    assert gaps[0]["category"] == "ความน่าเชื่อถือ"
    assert gaps[0]["missed_query_count"] == 1


def test_opportunity_accepts_plain_string_focal():
    gaps = OpportunityFinder.identify_gaps("Shopee", {"brands": []}, [])
    assert isinstance(gaps, list)


# --- deterministic mock across processes ----------------------------------
def test_mock_engine_deterministic_across_processes():
    code = (
        "from src.engines.mock_engine import MockObservationEngine;"
        "o=MockObservationEngine().observe(query_id='q1',query_text='ซื้อสกินแคร์ที่ไหนดี',target_brands=['Shopee','Konvy','Watsons']);"
        "print([(m.brand_name,m.rank,m.sentiment) for m in o.brand_mentions])"
    )
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    a = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=_REPO, env=env)
    env["PYTHONHASHSEED"] = "1"
    b = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=_REPO, env=env)
    assert a.stdout == b.stdout and a.stdout.strip() != "[]"


# --- 5.8 API input safety --------------------------------------------------
def test_scan_rejects_out_of_range_count():
    assert client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 0}).status_code == 422
    assert client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 99999}).status_code == 422


def test_scan_rejects_unknown_engine():
    r = client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "engine_type": "gpt5"})
    assert r.status_code == 422


def test_scan_rejects_unknown_vertical():
    r = client.post("/api/v1/scan", json={"vertical_id": "does_not_exist", "engine_type": "mock", "count": 5})
    assert r.status_code == 404
