"""Final acceptance scenario (master prompt section 19).

User opens dashboard -> (auth) -> selects vertical -> triggers scan ->
backend validates -> engine runs -> observations get unique ids -> provenance
correct -> data persisted -> analytics read canonical data -> API returns result
-> dashboard can render -> data mode is surfaced -> export works -> failures are
never shown as successful insight.
"""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from src.api import app
from src.storage import DuckDBStore

client = TestClient(app)


def test_full_scenario_mock(monkeypatch, tmp_path):
    # --- auth: enforced mode rejects unauthenticated writes ---
    monkeypatch.setenv("AIBT_API_KEYS", "acc-key")
    assert client.post("/api/v1/scan", json={"vertical_id": "ecommerce_retail_th", "count": 5}).status_code == 401
    h = {"X-API-Key": "acc-key"}

    # --- select vertical ---
    verticals = client.get("/api/v1/verticals", headers=h).json()
    assert any(v["vertical_id"] == "ev_automotive_th" for v in verticals)

    # --- validation: bad params never reach the engine ---
    assert (
        client.post("/api/v1/scan", json={"vertical_id": "ev_automotive_th", "count": 0}, headers=h).status_code == 422
    )
    assert client.post("/api/v1/scan", json={"vertical_id": "nope", "count": 5}, headers=h).status_code == 404

    # --- trigger scan ---
    start = client.post(
        "/api/v1/scan",
        json={"vertical_id": "ev_automotive_th", "engine_type": "mock", "count": 12},
        headers=h,
    )
    assert start.status_code == 200
    assert start.json()["data_mode"] == "synthetic"
    task_id = start.json()["task_id"]

    prog = client.get(f"/api/v1/scan/{task_id}/progress", headers=h).json()
    assert prog["status"] == "COMPLETED"
    stats = prog["run_stats"]
    assert stats["successful_observations"] == 12
    assert stats["persistence_failures"] == 0
    assert stats["persisted_observations_reloaded"] == 12
    run_id = prog["run_id"]

    # --- provenance + unique ids in the persisted store ---
    from src.api import DATA_DIR

    store = DuckDBStore(db_path=f"{DATA_DIR}/intelligence.duckdb")
    prov = store.fetch_df(
        "SELECT observation_id, provider, answer_surface FROM fact_observation WHERE run_id = ?", [run_id]
    )
    assert len(prov) == 12
    assert prov["observation_id"].nunique() == 12
    assert set(prov["provider"]) == {"mock"}
    assert set(prov["answer_surface"]) == {"synthetic"}

    # --- analytics came from the canonical store; API returns it ---
    data = client.get("/api/v1/metrics/ev_automotive_th", headers=h).json()
    assert data["run_id"] == run_id
    assert data["data_mode"] == "synthetic"  # surfaced so the UI can label it
    assert data["metrics"]["brands"]
    assert data["metrics"]["primary_surface"] in ("generative_answer", "all_surfaces_combined")

    # --- export works ---
    csv_resp = client.get("/api/v1/export/ev_automotive_th?format=csv", headers=h)
    assert csv_resp.status_code == 200
    rows = list(csv.reader(io.StringIO(csv_resp.text)))
    assert rows[0][:2] == ["Rank", "Brand"]
    assert len(rows) >= 2

    json_resp = client.get("/api/v1/export/ev_automotive_th?format=json", headers=h)
    assert json_resp.json()["run_id"] == run_id


def test_failed_engine_is_not_reported_as_successful_insight(monkeypatch):
    """gemini with no API key -> every observation fails -> run raises ->
    task FAILED, not COMPLETED-with-empty-metrics."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AIBT_API_KEYS", raising=False)

    start = client.post(
        "/api/v1/scan",
        json={"vertical_id": "ecommerce_retail_th", "engine_type": "gemini", "count": 4},
    )
    assert start.status_code == 200
    task_id = start.json()["task_id"]
    prog = client.get(f"/api/v1/scan/{task_id}/progress").json()

    assert prog["status"] == "FAILED"
    assert "0 persisted observations" in prog["error"]
    assert prog.get("result") is None  # no fabricated insight surfaced
