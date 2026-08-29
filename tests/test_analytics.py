import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics.citation_graph import CitationInfluenceAnalyzer
from src.analytics.claim_intelligence import ClaimIntelligenceEngine
from src.analytics.metrics import MarketMetricsEngine
from src.analytics.opportunity import OpportunityFinder


def test_metrics_calculation():
    sample_obs = [
        {
            "query_id": "q1",
            "brand_mentions": [
                {
                    "brand_name": "Shopee",
                    "mentioned": True,
                    "rank": 1,
                    "sentiment": "positive",
                    "recommendation_intent": "strongly_recommended",
                },
                {
                    "brand_name": "Lazada",
                    "mentioned": True,
                    "rank": 2,
                    "sentiment": "neutral",
                    "recommendation_intent": "recommended",
                },
            ],
        },
        {
            "query_id": "q2",
            "brand_mentions": [
                {
                    "brand_name": "Shopee",
                    "mentioned": True,
                    "rank": 1,
                    "sentiment": "positive",
                    "recommendation_intent": "recommended",
                }
            ],
        },
    ]

    res = MarketMetricsEngine.calculate_share_of_voice(sample_obs)
    assert res["total_queries"] == 2
    brands = {b["brand"]: b for b in res["brands"]}
    assert brands["Shopee"]["share_of_voice_pct"] == 100.0
    assert brands["Lazada"]["share_of_voice_pct"] == 50.0
    assert brands["Shopee"]["average_rank"] == 1.0


def test_opportunity_finder():
    metrics = {"brands": []}
    obs = [
        {
            "query_text": "ซื้อเครื่องสำอางแท้ที่ไหนดี?",
            "category": "ความน่าเชื่อถือ",
            "brand_mentions": [{"brand_name": "Konvy", "rank": 1, "sentiment": "positive", "mentioned": True}],
        }
    ]
    gaps = OpportunityFinder.identify_gaps("Shopee", metrics, obs)
    assert len(gaps) == 1
    assert "CATEGORY_VISIBILITY_GAP" in gaps[0]["type"]
    assert gaps[0]["category"] == "ความน่าเชื่อถือ"


def test_claim_intelligence_audit():
    obs = [
        {
            "query_id": "q_test",
            "brand_mentions": [
                {
                    "brand_name": "Shopee Thailand",
                    "key_strengths_mentioned": ["มีโค้ดส่งฟรีเยอะมาก"],
                    "price_or_deal_claims": [],
                }
            ],
        }
    ]
    claims = ClaimIntelligenceEngine.audit_claims(obs)
    assert len(claims) == 1
    assert claims[0]["audit_verdict"] == "CONDITIONAL"


def test_citation_influence():
    obs = [
        {
            "brand_mentions": [{"brand_name": "Shopee", "mentioned": True}],
            "citations": [{"domain": "pantip.com"}, {"domain": "wongnai.com"}],
        }
    ]
    cit = CitationInfluenceAnalyzer.analyze_influence(obs)
    assert cit["total_citations"] == 2
    assert cit["unique_domains"] == 2


def test_market_strategy_simulator():
    from src.analytics.simulator import MarketStrategySimulator

    sim = MarketStrategySimulator.simulate_strategy(
        target_brand="Shopee Thailand",
        current_sov_pct=50.0,
        current_nrs=20.0,
        strategy_levers=["forum_advocacy", "official_mall_guarantee"],
    )
    assert sim["simulated"]["share_of_voice_pct"] > 50.0
    assert sim["simulated"]["net_recommendation_score"] > 20.0
    assert "pantip.com" in sim["activated_citation_nodes"]
