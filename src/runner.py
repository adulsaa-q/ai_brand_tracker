# src/runner.py
from __future__ import annotations

import json
import os
import sys
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
from src.logger import get_logger
from src.storage import DuckDBStore, SQLiteStore
from src.universe import QueryUniverseGenerator
from src.universe.temporal_events import ThailandTemporalEngine

logger = get_logger("runner")


def run_intelligence_pipeline(
    vertical_id: str = "ecommerce_retail_th",
    count: int = 30,
    seed: int = 42,
    engine_type: str = "mock",
    db_path: str = "data/intelligence.db",
    duckdb_path: str = "data/intelligence.duckdb",
    include_control: bool = True,
    progress_callback: Any = None,
) -> dict[str, Any]:
    logger.info(
        f"Initializing AI Market Intelligence Pipeline [Vertical: {vertical_id}, Engine: {engine_type.upper()}]..."
    )

    sqlite_store = SQLiteStore(db_path=db_path)
    duckdb_store = DuckDBStore(db_path=duckdb_path)

    with open("config/entities.yaml", encoding="utf-8") as f:
        entities_data = yaml.safe_load(f)

    target_vertical = None
    for v in entities_data.get("verticals", []):
        if v["vertical_id"] == vertical_id:
            target_vertical = v
            break

    if not target_vertical:
        target_vertical = entities_data["verticals"][0]
        vertical_id = target_vertical["vertical_id"]

    brands = [b["name"] for b in target_vertical.get("brands", [])]
    focal_brand = target_vertical.get("focal_brand", brands[0] if brands else "focal")

    # Ingest Brands into Lakehouse Dimensions
    for b in target_vertical.get("brands", []):
        duckdb_store.insert_brand(
            brand_id=b["id"],
            name=b["name"],
            vertical=vertical_id,
            is_focal=b.get("is_focal_brand", False),
            aliases=b.get("aliases", []),
            domains=b.get("official_domains", []),
        )
        sqlite_store.insert_brand(
            brand_id=b["id"],
            name=b["name"],
            vertical=vertical_id,
            is_focal=b.get("is_focal_brand", False),
            aliases=b.get("aliases", []),
            domains=b.get("official_domains", []),
        )

    active_events = ThailandTemporalEngine.get_active_events()
    logger.info(f"Active Thailand Temporal Contexts: {[e['name_th'] for e in active_events]}")

    generator = QueryUniverseGenerator()
    queries = generator.generate_queries(
        vertical_id=vertical_id, count=count, seed=seed, include_control=include_control
    )
    logger.info(
        f"Generated {len(queries)} Thai Consumer Queries (Control: {sum(1 for q in queries if q.get('is_control_set'))}, Exploratory: {sum(1 for q in queries if not q.get('is_control_set'))})."
    )

    from src.engines import EngineFactory

    engine = EngineFactory.create(engine_type=engine_type)

    observations = []
    total_q = len(queries)
    logger.info(f"Executing AI Observations with [{engine_type.upper()}]...")
    for idx, q in enumerate(queries):
        if progress_callback:
            progress_callback(idx + 1, total_q, q["text_th"])

        obs = engine.observe(query_id=q["query_id"], query_text=q["text_th"], target_brands=brands)
        obs_dict = obs.model_dump()
        obs_dict["category"] = q.get("category", "General")
        obs_dict["is_control_set"] = q.get("is_control_set", False)
        obs_dict["vertical_id"] = vertical_id
        observations.append(obs_dict)

        try:
            duckdb_store.insert_observation(obs_dict)
            sqlite_store.insert_raw_observation(
                query_id=obs_dict["query_id"],
                query_text=obs_dict["query_text"],
                engine_provider=obs_dict["engine_provider"],
                model_name=obs_dict["model_name"],
                raw_text=obs_dict.get("response_raw_text", ""),
                latency_ms=obs_dict.get("response_latency_ms", 0),
                mentions=obs_dict.get("brand_mentions", []),
                citations=obs_dict.get("citations", []),
            )
        except Exception as e:
            logger.warning(f"Failed to persist observation {obs_dict.get('observation_id')}: {e}")

    # 1. Share of Voice & Ranking
    metrics = MarketMetricsEngine.calculate_share_of_voice(observations)
    # 2. Competitor Gaps & Opportunities
    opportunities = OpportunityFinder.identify_gaps(focal_brand, metrics, observations)
    # 3. Citation Graph
    citations = CitationInfluenceAnalyzer.analyze_influence(observations)
    # 4. Claim Intelligence
    claims = ClaimIntelligenceEngine.audit_claims(observations)
    # 5. AI Information Freshness & Lag
    lag = AIInformationLagTracker.measure_knowledge_freshness(observations)

    os.makedirs("data", exist_ok=True)
    summary_path = f"data/latest_run_summary_{vertical_id}.json"
    result_data = {
        "vertical_id": vertical_id,
        "vertical_name": target_vertical.get("name_th", ""),
        "total_queries": len(queries),
        "engine_type": engine_type,
        "metrics": metrics,
        "opportunities": opportunities,
        "citations_analysis": citations,
        "claims_audit": claims,
        "information_lag": lag,
        "observations": observations,
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    # Also update general latest_run_summary.json
    with open("data/latest_run_summary.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Pipeline completed successfully for {vertical_id}. Summary persisted to {summary_path}")
    return result_data


if __name__ == "__main__":
    run_intelligence_pipeline(vertical_id="ecommerce_retail_th", count=10, engine_type="mock")
