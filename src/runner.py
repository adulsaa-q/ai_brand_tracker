# src/runner.py
from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any

import yaml

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics import (
    AIInformationLagTracker,
    CitationInfluenceAnalyzer,
    ClaimIntelligenceEngine,
    MarketMetricsEngine,
    OpportunityFinder,
)
from src.analytics.repository import AnalyticsRepository
from src.brands import resolve_focal_brand
from src.exceptions import EngineError
from src.ids import new_run_id
from src.logger import get_logger
from src.storage import DuckDBStore
from src.universe import QueryUniverseGenerator
from src.universe.temporal_events import ThailandTemporalEngine

logger = get_logger("runner")

ENTITIES_PATH = os.getenv("ENTITIES_PATH", "config/entities.yaml")
DATA_DIR = os.getenv("DATA_DIR", "data")


def _atomic_write_json(path: str, payload: dict) -> None:
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def run_intelligence_pipeline(
    vertical_id: str = "ecommerce_retail_th",
    count: int = 30,
    seed: int = 42,
    engine_type: str = "mock",
    duckdb_path: str | None = None,
    include_control: bool = True,
    progress_callback: Any = None,
    entities_path: str | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    run_id = new_run_id()
    entities_path = entities_path or ENTITIES_PATH
    output_dir = output_dir or DATA_DIR
    duckdb_path = duckdb_path or os.path.join(output_dir, "intelligence.duckdb")
    logger.info("Starting run %s [vertical=%s engine=%s count=%s]", run_id, vertical_id, engine_type.upper(), count)

    duckdb_store = DuckDBStore(db_path=duckdb_path)

    with open(entities_path, encoding="utf-8") as f:
        entities_data = yaml.safe_load(f) or {"verticals": []}

    target_vertical = next((v for v in entities_data.get("verticals", []) if v["vertical_id"] == vertical_id), None)
    if not target_vertical:
        if not entities_data.get("verticals"):
            raise ValueError(f"No verticals defined in {entities_path}")
        target_vertical = entities_data["verticals"][0]
        vertical_id = target_vertical["vertical_id"]
        logger.warning("Vertical not found; falling back to %s", vertical_id)

    brands = [b["name"] for b in target_vertical.get("brands", [])]
    focal = resolve_focal_brand(target_vertical)
    logger.info("Focal brand resolved: %s (id=%s)", focal.name, focal.brand_id)

    for b in target_vertical.get("brands", []):
        duckdb_store.insert_brand(
            brand_id=b["id"],
            name=b["name"],
            vertical=vertical_id,
            is_focal=focal.matches(b.get("id", "")) or focal.matches(b.get("name", "")),
            aliases=b.get("aliases", []),
            domains=b.get("official_domains", []),
        )

    active_events = [
        {k: v for k, v in e.items() if isinstance(v, (str, int, float, list))}
        for e in ThailandTemporalEngine.get_active_events()
    ]
    logger.info("Active Thailand temporal contexts: %s", [e.get("name_th") for e in active_events])

    generator = QueryUniverseGenerator(entities_path=entities_path)
    queries = generator.generate_queries(
        vertical_id=vertical_id, count=count, seed=seed, include_control=include_control
    )
    for q in queries:
        q.setdefault("vertical_id", vertical_id)
        duckdb_store.insert_query(q)
    logger.info(
        "Generated %d queries (control=%d exploratory=%d)",
        len(queries),
        sum(1 for q in queries if q.get("is_control_set")),
        sum(1 for q in queries if not q.get("is_control_set")),
    )

    from src.engines import EngineFactory

    engine = EngineFactory.create(engine_type=engine_type)

    stats = {
        "requested_observations": len(queries),
        "successful_observations": 0,
        "persistence_failures": 0,
        "provider_errors": 0,
        "parse_failures": 0,
        "no_structured_output": 0,
    }
    observations: list[dict[str, Any]] = []
    total_q = len(queries)

    for idx, q in enumerate(queries):
        if progress_callback:
            progress_callback(idx + 1, total_q, q["text_th"])

        try:
            obs = engine.observe(query_id=q["query_id"], query_text=q["text_th"], target_brands=brands)
        except EngineError as exc:
            stats["provider_errors"] += 1
            logger.error("Provider error on %s: %s", q["query_id"], exc, exc_info=False)
            continue

        obs_dict = obs.model_dump()
        obs_dict["run_id"] = run_id
        obs_dict["category"] = q.get("category", "General")
        obs_dict["is_control_set"] = q.get("is_control_set", False)
        obs_dict["vertical_id"] = vertical_id

        if obs_dict.get("parse_status") == "parse_error":
            stats["parse_failures"] += 1
        elif obs_dict.get("parse_status") == "no_structured_output":
            stats["no_structured_output"] += 1

        try:
            duckdb_store.insert_observation(obs_dict)
        except Exception:
            stats["persistence_failures"] += 1
            logger.exception("Persistence failure for observation %s", obs_dict.get("observation_id"))
            continue

        observations.append(obs_dict)
        stats["successful_observations"] += 1

    logger.info("Run %s stats: %s", run_id, stats)

    if stats["successful_observations"] == 0:
        raise RuntimeError(
            f"Run {run_id} produced 0 persisted observations "
            f"(provider_errors={stats['provider_errors']}, persistence_failures={stats['persistence_failures']})"
        )
    if stats["persistence_failures"] > 0:
        logger.error("Run %s had %d persistence failures", run_id, stats["persistence_failures"])

    # Canonical analytics input: read back what was actually persisted to DuckDB
    # (not the in-memory list). See docs/adr/0001.
    persisted = AnalyticsRepository(duckdb_store).load_observations(run_id)
    logger.info("Reloaded %d observations from DuckDB for analytics", len(persisted))
    stats["persisted_observations_reloaded"] = len(persisted)
    stats["retries_total"] = sum(o.get("retry_count", 0) for o in observations)
    stats["surfaces"] = sorted({o.get("answer_surface", "unknown") for o in persisted})

    metrics = MarketMetricsEngine.build_report(persisted)
    opportunities = OpportunityFinder.identify_gaps(focal, metrics, persisted)
    citations = CitationInfluenceAnalyzer.analyze_influence(persisted)
    claims = ClaimIntelligenceEngine.audit_claims(persisted)
    lag = AIInformationLagTracker.measure_knowledge_freshness(persisted)

    result_data = {
        "run_id": run_id,
        "vertical_id": vertical_id,
        "vertical_name": target_vertical.get("name_th", ""),
        "focal_brand": {"id": focal.brand_id, "name": focal.name},
        "engine_type": engine_type,
        "data_mode": "synthetic" if engine_type == "mock" else "live",
        "total_queries": len(queries),
        "run_stats": stats,
        "active_events": active_events,
        "metrics": metrics,
        "opportunities": opportunities,
        "citations_analysis": citations,
        "claims_audit": claims,
        "information_lag": lag,
        "observations": persisted,
    }

    os.makedirs(output_dir, exist_ok=True)
    _atomic_write_json(os.path.join(output_dir, f"run_{run_id}.json"), result_data)
    _atomic_write_json(os.path.join(output_dir, f"latest_run_summary_{vertical_id}.json"), result_data)
    _atomic_write_json(os.path.join(output_dir, "latest_run_summary.json"), result_data)

    logger.info("Run %s complete for %s", run_id, vertical_id)
    return result_data


if __name__ == "__main__":
    run_intelligence_pipeline(vertical_id="ecommerce_retail_th", count=10, engine_type="mock")
