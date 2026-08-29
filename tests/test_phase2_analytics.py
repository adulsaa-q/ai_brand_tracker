"""Phase 2: source-of-truth analytics, engine semantics, prompt registry, retry."""

from __future__ import annotations

import io
import urllib.error

import pytest

from src.analytics.metrics import MarketMetricsEngine
from src.analytics.repository import AnalyticsRepository
from src.engines import _http
from src.engines._parsing import parse_brand_mentions
from src.exceptions import EngineError, RateLimitExceededError
from src.prompts import get_prompt
from src.runner import run_intelligence_pipeline
from src.storage import DuckDBStore


# --- 7.1 engine semantic contract ----------------------------------------
def _obs(surface, qid, brand, rank):
    return {
        "query_id": qid,
        "answer_surface": surface,
        "brand_mentions": [{"brand_name": brand, "mentioned": True, "rank": rank, "sentiment": "positive"}],
        "citations": [],
    }


def test_metrics_do_not_mix_answer_surfaces():
    observations = [
        _obs("generative_answer", "q1", "Shopee", 1),
        _obs("generative_answer", "q2", "Shopee", 1),
        _obs("organic_serp", "q1", "Lazada", 1),
    ]
    report = MarketMetricsEngine.build_report(observations)
    assert report["primary_surface"] == "generative_answer"
    assert {b["brand"] for b in report["brands"]} == {"Shopee"}  # SERP-only Lazada excluded from headline
    assert set(report["surfaces_present"]) == {"generative_answer", "organic_serp"}
    assert "organic_serp" in report["by_surface"]
    assert report["by_surface"]["organic_serp"]["brands"][0]["brand"] == "Lazada"


def test_metrics_falls_back_when_no_generative_surface():
    report = MarketMetricsEngine.build_report([_obs("synthetic", "q1", "Shopee", 1)])
    assert report["primary_surface"] == "all_surfaces_combined"
    assert report["total_queries"] == 1


# --- 7 canonical source of truth: analytics read from DuckDB --------------
def test_analytics_input_comes_from_duckdb(tmp_path):
    out = tmp_path / "o"
    result = run_intelligence_pipeline(
        vertical_id="ecommerce_retail_th", count=10, engine_type="mock", output_dir=str(out)
    )
    run_id = result["run_id"]
    store = DuckDBStore(db_path=str(out / "intelligence.duckdb"))
    reloaded = AnalyticsRepository(store).load_observations(run_id)

    # the summary's observations are exactly what the repository returns
    assert len(result["observations"]) == len(reloaded)
    assert result["run_stats"]["persisted_observations_reloaded"] == result["run_stats"]["successful_observations"]
    assert {o["observation_id"] for o in result["observations"]} == {o["observation_id"] for o in reloaded}
    # every reloaded observation carries its query dimension (join worked)
    assert all(o["category"] for o in reloaded)


# --- 7.3 prompt registry -------------------------------------------------
def test_prompt_registry_versions_are_stamped():
    p = get_prompt("gemini.brand_audit")
    assert p.id == f"{p.name}@{p.version}"
    with pytest.raises(KeyError):
        get_prompt("nope.not.a.prompt")


# --- 7.2 structured output parsing never silently empties ----------------
def test_parse_error_is_distinct_from_empty_result():
    mentions, status = parse_brand_mentions('```json\n{"brand_mentions": []}\n```', query_id="q")
    assert status == "ok" and mentions == []  # model genuinely said "nobody mentioned"

    _, status = parse_brand_mentions("```json\n{not valid\n```", query_id="q")
    assert status == "parse_error"  # technical failure, NOT "nobody mentioned"


# --- 7.4 provider reliability policy ------------------------------------
def test_request_json_retries_then_raises_rate_limit(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b""))

    monkeypatch.setattr(_http.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_http, "_sleep", lambda a: None)

    with pytest.raises(RateLimitExceededError):
        _http.request_json("https://x.test", engine="test", max_retries=2)
    assert calls["n"] == 3  # initial + 2 retries


def test_request_json_does_not_retry_on_4xx(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, io.BytesIO(b""))

    monkeypatch.setattr(_http.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_http, "_sleep", lambda a: None)

    with pytest.raises(EngineError):
        _http.request_json("https://x.test", engine="test", max_retries=2)
    assert calls["n"] == 1


def test_request_json_succeeds_after_transient_5xx(monkeypatch):
    seq = [
        urllib.error.HTTPError("u", 503, "x", {}, io.BytesIO(b"")),
        _FakeResp(b'{"ok": true}'),
    ]
    monkeypatch.setattr(_http.urllib.request, "urlopen", lambda req, timeout=None: _pop(seq))
    monkeypatch.setattr(_http, "_sleep", lambda a: None)
    data, retries = _http.request_json("https://x.test", engine="test")
    assert data == {"ok": True} and retries == 1


class _FakeResp:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


def _pop(seq):
    item = seq.pop(0)
    if isinstance(item, Exception):
        raise item
    return item


# --- alias-aware brand detection (serper/tavily substring surfaces) --------
def test_serper_matches_brand_aliases(monkeypatch):
    from src.engines import serper_engine

    fake = {
        "organic": [
            {"link": "https://x.th/a", "title": "รีวิว ช้อปปี้ ส่งไว", "snippet": "ซื้อที่ ช้อปปี้ ดีสุด"},
            {"link": "https://y.th/b", "title": "Lazada promo", "snippet": "แอพน้ำเงิน"},
        ]
    }
    monkeypatch.setattr(serper_engine, "request_json", lambda *a, **k: (fake, 0))
    eng = serper_engine.SerperGoogleEngine(api_key="k")
    obs = eng.observe(
        query_id="q",
        query_text="ซื้อของที่ไหนดี",
        target_brands=["Shopee Thailand", "Lazada Thailand"],
        brand_aliases={"Shopee Thailand": ["ช้อปปี้", "shopee"], "Lazada Thailand": ["ลาซาด้า", "แอพน้ำเงิน"]},
    )
    m = {x.brand_name: x for x in obs.brand_mentions}
    assert m["Shopee Thailand"].mentioned and m["Shopee Thailand"].rank == 1
    assert m["Lazada Thailand"].mentioned and m["Lazada Thailand"].rank == 2  # matched via alias only
