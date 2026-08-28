import os
import sys
import json
import yaml

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.universe import QueryUniverseGenerator
from src.universe.temporal_events import ThailandTemporalEngine
from src.engines import MockObservationEngine, GeminiObservationEngine, OpenRouterEngine
from src.storage import SQLiteStore
from src.analytics import (
    MarketMetricsEngine,
    OpportunityFinder,
    CitationInfluenceAnalyzer,
    ClaimIntelligenceEngine,
    AIInformationLagTracker
)

def run_intelligence_pipeline(
    count: int = 10,
    seed: int = 42,
    engine_type: str = "mock",
    db_path: str = "data/intelligence.db"
):
    print(f"🚀 Initializing Thailand AI Market Intelligence Pipeline [Engine: {engine_type.upper()}]...")
    
    store = SQLiteStore(db_path=db_path)
    with open("config/entities.yaml", "r", encoding="utf-8") as f:
        entities = yaml.safe_load(f)
    
    brands = [b["name"] for b in entities["verticals"][0]["brands"]]
    focal_brand = entities["verticals"][0].get("focal_brand", "shopee")

    active_events = ThailandTemporalEngine.get_active_events()
    print(f"📅 Active Thailand Temporal Contexts: {[e['name_th'] for e in active_events]}")

    generator = QueryUniverseGenerator()
    queries = generator.generate_queries(count=count, seed=seed)
    print(f"✅ Generated {len(queries)} Thai Consumer Queries.")

    if engine_type == "gemini":
        engine = GeminiObservationEngine()
    elif engine_type == "openrouter":
        engine = OpenRouterEngine()
    else:
        engine = MockObservationEngine(model_name="mock-gemini-2.5")

    observations = []
    print("⚡ Executing AI Observations...")
    for q in queries:
        obs = engine.observe(query_id=q["query_id"], query_text=q["text_th"], target_brands=brands)
        obs_dict = obs.model_dump()
        obs_dict["category"] = q["category"]
        observations.append(obs_dict)

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
        json.dump({
            "metrics": metrics,
            "opportunities": opportunities,
            "citations_analysis": citations,
            "claims_audit": claims,
            "information_lag": lag,
            "active_events": active_events,
            "observations": observations
        }, f, ensure_ascii=False, indent=2)

    print(f"🎉 Pipeline Completed! Deep Results saved to {summary_path}")
    return metrics, opportunities

if __name__ == "__main__":
    run_intelligence_pipeline(count=10, seed=100, engine_type="mock")
