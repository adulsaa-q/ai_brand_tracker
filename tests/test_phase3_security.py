"""Phase 3: auth, abuse protection, health."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

import src.security as security


@pytest.fixture
def client():
    return TestClient(importlib.import_module("src.api").app)


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv("AIBT_API_KEYS", "secret-a,secret-b")
    monkeypatch.setattr(security, "_warned_open", True)
    yield


def test_open_mode_allows_writes_but_reports_it(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["auth_mode"] == "open"
    # write still allowed in open mode
    assert client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 3}).status_code == 200


def test_enforced_mode_rejects_unauthenticated_write(client, keyed):
    assert client.get("/api/v1/health").json()["auth_mode"] == "enforced"
    r = client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 3})
    assert r.status_code == 401
    r = client.post(
        "/api/v1/scan",
        json={"vertical_id": "ecommerce_retail_th", "count": 3},
        headers={"X-API-Key": "wrong"},
    )
    assert r.status_code == 401


def test_enforced_mode_accepts_valid_key(client, keyed):
    r = client.post(
        "/api/v1/scan",
        json={"vertical_id": "ecommerce_retail_th", "count": 3},
        headers={"Authorization": "Bearer secret-b"},
    )
    assert r.status_code == 200


def test_reads_open_unless_require_auth(client, keyed, monkeypatch):
    assert client.get("/api/v1/verticals").status_code == 200  # reads open by default
    monkeypatch.setenv("AIBT_REQUIRE_AUTH", "true")
    assert client.get("/api/v1/verticals").status_code == 401
    assert client.get("/api/v1/verticals", headers={"X-API-Key": "secret-a"}).status_code == 200


def test_scan_concurrency_limit(client, monkeypatch):
    monkeypatch.setenv("AIBT_MAX_CONCURRENT_SCANS", "0")
    r = client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 3})
    assert r.status_code == 429


def test_daily_quota_limit(client, monkeypatch):
    monkeypatch.setenv("AIBT_MAX_RUNS_PER_DAY", "0")
    r = client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 3})
    assert r.status_code == 429


def test_health_reports_dependencies(client):
    body = client.get("/api/v1/health").json()
    assert body["liveness"] == "ok"
    assert "duckdb" in body["dependencies"]
    assert "entities_config" in body["dependencies"]
    assert "scan_limiter" in body


def test_vertical_input_validation(client):
    # empty brands list rejected
    bad = {
        "vertical_id": "bad vertical",  # space not allowed
        "name_th": "x",
        "name_en": "x",
        "focal_brand": "x",
        "brands": [],
    }
    assert client.post("/api/v1/verticals", json=bad).status_code == 422
