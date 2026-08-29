import json
import os
import sys

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
    count: int = 15,
    seed: int = 42,
    engine_type: str = "mock",
    db_path: str = "data/intelligence.db",
    duckdb_path: str = "data/intelligence.duckdb",
    include_control: bool = True,
):
    logger.info(f"Initializing Thailand AI Market Intelligence Pipeline [Engine: {engine_type.upper()}]...")

    sqlite_store = SQLiteStore(db_path=db_path)
    duckdb_store = DuckDBStore(db_path=duckdb_path)

    with open("config/entities.yaml", encoding="utf-8") as f:
        entities = yaml.safe_load(f)

    brands = [b["name"] for b in entities["verticals"][0]["brands"]]
    focal_brand = entities["verticals"][0].get("focal_brand", "shopee")

    active_events = ThailandTemporalEngine.get_active_events()
    logger.info(f"Active Thailand Temporal Contexts: {[e['name_th'] for e in active_events]}")

    generator = QueryUniverseGenerator()
    queries = generator.generate_queries(count=count, seed=seed, include_control=include_control)
    logger.info(
        f"Generated {len(queries)} Thai Consumer Queries (Control: {sum(1 for q in queries if q.get('is_control_set'))}, Exploratory: {sum(1 for q in queries if not q.get('is_control_set'))})."
    )

    from src.engines import EngineFactory

    engine = EngineFactory.create(engine_type=engine_type)

    observations = []
    logger.info(f"Executing AI Observations with [{engine_type.upper()}]...")
    for q in queries:
        obs = engine.observe(query_id=q["query_id"], query_text=q["text_th"], target_brands=brands)
        obs_dict = obs.model_dump()
        obs_dict["category"] = q["category"]
        obs_dict["is_control_set"] = q.get("is_control_set", False)
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
    # 2. Competitor Gaps
    opportunities = OpportunityFinder.identify_gaps(focal_brand, metrics, observations)
    # 3. Citation Graph
    citations = CitationInfluenceAnalyzer.analyze_influence(observations)
    # 4. Claim Intelligence
    claims = ClaimIntelligenceEngine.audit_claims(observations)
    # 5. AI Information Freshness & Lag
    lag = AIInformationLagTracker.measure_knowledge_freshness(observations)

    os.makedirs("data", exist_ok=True)
    summary_path = "data/latest_run_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metrics": metrics,
                "opportunities": opportunities,
                "citations_analysis": citations,
                "claims_audit": claims,
                "information_lag": lag,
                "active_events": active_events,
                "observations": observations,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    logger.info(f"Pipeline Completed! Deep Results saved to {summary_path}")
    return metrics, opportunities


if __name__ == "__main__":
    run_intelligence_pipeline(count=15, seed=100, engine_type="mock", include_control=True)
