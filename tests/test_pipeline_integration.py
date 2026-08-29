"""Phase 1 exit gate: end-to-end pipeline -> storage -> analytics reconciliation.

Proves the chain Query -> Engine -> Observation -> DuckDB -> Analytics -> Summary
with the row counts at each stage reconciling, not just "a key exists".
"""

from __future__ import annotations

from src.runner import run_intelligence_pipeline
from src.storage import DuckDBStore


def _run(tmp_path, **kw):
    out = tmp_path / "out"
    result = run_intelligence_pipeline(
        vertical_id=kw.get("vertical_id", "ecommerce_retail_th"),
        count=kw.get("count", 10),
        seed=kw.get("seed", 42),
        engine_type="mock",
        include_control=kw.get("include_control", True),
        output_dir=str(out),
    )
    store = DuckDBStore(db_path=str(out / "intelligence.duckdb"))
    return result, store, out


def test_pipeline_reconciles_across_stages(tmp_path):
    result, store, out = _run(tmp_path, count=14)
    run_id = result["run_id"]
    stats = result["run_stats"]

    # generation stage
    assert result["total_queries"] == 14
    assert stats["requested_observations"] == 14

    # persistence stage: every successful observation is in DuckDB, tagged with run_id
    assert stats["successful_observations"] == 14
    assert stats["persistence_failures"] == 0
    assert store.count_rows("fact_observation", run_id=run_id) == 14
    assert store.count_rows("dim_query") >= 14

    # mention + citation grain
    obs = result["observations"]
    expected_mentions = sum(len(o["brand_mentions"]) for o in obs)
    expected_citations = sum(len(o["citations"]) for o in obs)
    assert store.count_rows("fact_brand_mention", run_id=run_id) == expected_mentions
    assert store.count_rows("fact_citation", run_id=run_id) == expected_citations

    # referential integrity: every observation joins back to a query dimension row
    joined = store.fetch_df(
        "SELECT COUNT(*) c FROM fact_observation o WHERE o.run_id = ? "
        "AND o.query_id IN (SELECT query_id FROM dim_query)",
        [run_id],
    )
    assert int(joined.iloc[0]["c"]) == 14

    # provenance is honest and consistent
    prov = store.fetch_df("SELECT DISTINCT provider, answer_surface FROM fact_observation WHERE run_id = ?", [run_id])
    assert prov.to_dict("records") == [{"provider": "mock", "answer_surface": "synthetic"}]

    # analytics reads the same observations
    sov_total = result["metrics"]["total_queries"]
    assert sov_total == len({o["query_id"] for o in obs})

    # summary artifacts written atomically
    assert (out / f"run_{run_id}.json").exists()
    assert (out / "latest_run_summary_ecommerce_retail_th.json").exists()
    assert (out / "latest_run_summary.json").exists()
    assert result["data_mode"] == "synthetic"


def test_two_runs_do_not_clobber_each_other(tmp_path):
    r1, store, out = _run(tmp_path, count=8, seed=1)
    r2 = run_intelligence_pipeline(
        vertical_id="ev_automotive_th", count=8, seed=2, engine_type="mock", output_dir=str(out)
    )
    # both runs retained in the fact table
    assert store.count_rows("fact_observation", run_id=r1["run_id"]) == 8
    assert store.count_rows("fact_observation", run_id=r2["run_id"]) == 8
    # per-vertical summaries are independent
    assert (out / "latest_run_summary_ecommerce_retail_th.json").exists()
    assert (out / "latest_run_summary_ev_automotive_th.json").exists()


def test_deterministic_mock_run_is_reproducible(tmp_path):
    r1, *_ = _run(tmp_path / "a", count=10, seed=42)
    r2, *_ = _run(tmp_path / "b", count=10, seed=42)
    b1 = [(b["brand"], b["share_of_voice_pct"], b["average_rank"]) for b in r1["metrics"]["brands"]]
    b2 = [(b["brand"], b["share_of_voice_pct"], b["average_rank"]) for b in r2["metrics"]["brands"]]
    assert b1 == b2
