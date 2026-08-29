"""Phase 4: the exact request sequence the web dashboard performs.

The browser flow (dashboard/web/index.html) is:
  POST /api/v1/scan  -> {task_id}
  poll GET /api/v1/scan/{task_id}/progress until status COMPLETED|FAILED
  GET  /api/v1/metrics/{vertical_id}  -> adaptApiMetrics() renders it

These tests exercise that sequence and assert the response shapes the frontend
adapter depends on.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def _run_scan(vertical="ecommerce_retail_th", engine="mock", count=6):
    started = client.post(
        "/api/v1/scan",
        json={"vertical_id": vertical, "engine_type": engine, "count": count, "include_control_set": True},
    )
    assert started.status_code == 200
    task_id = started.json()["task_id"]
    # TestClient runs the BackgroundTask synchronously, so it is already done
    prog = client.get(f"/api/v1/scan/{task_id}/progress").json()
    assert prog["status"] in ("COMPLETED", "RUNNING", "QUEUED")
    return task_id, prog


def test_scan_progress_shape_matches_frontend_expectations():
    _, prog = _run_scan()
    for key in ("status", "progress_pct", "completed", "total", "current_query", "engine_type"):
        assert key in prog
    if prog["status"] == "COMPLETED":
        assert prog["progress_pct"] == 100.0
        assert prog["run_stats"]["successful_observations"] >= 1


def test_metrics_shape_matches_adaptApiMetrics():
    _run_scan(count=8)
    data = client.get("/api/v1/metrics/ecommerce_retail_th").json()

    # top-level fields adaptApiMetrics() reads
    assert data["run_id"] and data["vertical_id"] == "ecommerce_retail_th"
    assert data["data_mode"] in ("synthetic", "live")
    assert isinstance(data["focal_brand"], dict) and "name" in data["focal_brand"]

    # metrics.brands[*]
    brands = data["metrics"]["brands"]
    assert brands and all({"brand", "share_of_voice_pct", "average_rank"} <= set(b) for b in brands)
    assert "primary_surface" in data["metrics"]

    # citations_analysis.domain_rankings[*]
    for d in data["citations_analysis"]["domain_rankings"]:
        assert {"domain", "citation_count", "influence_share_pct"} <= set(d)

    # observations[*] used to build the query table
    for o in data["observations"][:3]:
        assert {"query_id", "query_text", "category", "brand_mentions", "citations"} <= set(o)

    # opportunities[*] used by the 4-stage renderer
    for opp in data["opportunities"]:
        assert {"title", "priority", "what_is_happening", "so_what", "now_what"} <= set(opp)


def test_metrics_pending_scan_shape_for_unscanned_vertical():
    data = client.get("/api/v1/metrics/real_estate_th_never_scanned").json()
    assert data["status"] == "PENDING_SCAN"
    assert data["data_mode"] == "none"
    assert data["metrics"]["brands"] == []  # frontend shows the "no data" state


def test_custom_workspace_flow_create_then_scan():
    payload = {
        "vertical_id": "cw_testbrand",
        "name_th": "TestBrand — สกินแคร์",
        "name_en": "TestBrand workspace",
        "focal_brand": "TestBrand",
        "categories": ["สกินแคร์"],
        "brands": [
            {"id": "testbrand", "name": "TestBrand", "is_focal_brand": True},
            {"id": "rivalco", "name": "RivalCo", "is_focal_brand": False},
        ],
    }
    assert client.post("/api/v1/verticals", json=payload).json()["status"] in ("CREATED", "UPDATED")
    _run_scan(vertical="cw_testbrand", count=6)
    data = client.get("/api/v1/metrics/cw_testbrand").json()
    assert data["run_id"]
    assert {b["brand"] for b in data["metrics"]["brands"]} <= {"TestBrand", "RivalCo"}
    assert data["focal_brand"]["name"] == "TestBrand"


def test_scan_can_be_cancelled():
    """Cooperative cancel: mock is instant so we mostly assert the endpoint
    contract and that an already-finished task reports that."""
    started = client.post(
        "/api/v1/scan",
        json={"vertical_id": "ecommerce_retail_th", "engine_type": "mock", "count": 6},
    )
    task_id = started.json()["task_id"]
    r = client.post(f"/api/v1/scan/{task_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] in ("CANCELLING", "COMPLETED", "CANCELLED")
    assert client.post("/api/v1/scan/does_not_exist/cancel").status_code == 404


def test_runner_stops_early_on_cancel(tmp_path):
    from src.runner import run_intelligence_pipeline

    calls = {"n": 0}

    def cancel_after_3():
        calls["n"] += 1
        return calls["n"] > 3

    result = run_intelligence_pipeline(
        vertical_id="ecommerce_retail_th",
        count=20,
        engine_type="mock",
        output_dir=str(tmp_path),
        cancel_check=cancel_after_3,
    )
    assert result["run_stats"]["cancelled"] is True
    assert result["run_stats"]["successful_observations"] == 3
    assert result["status"] == "CANCELLED_PARTIAL"
