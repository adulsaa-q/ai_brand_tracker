# src/analytics/simulator.py
from __future__ import annotations

from typing import Any


class MarketStrategySimulator:
    """Simulates market intervention scenarios and forecasts AI visibility impact (What-If Analysis)."""

    LEVER_WEIGHTS = {
        "forum_advocacy": {"sov_impact": 0.15, "nrs_impact": 0.20, "top_node": "pantip.com"},
        "creator_unboxing": {"sov_impact": 0.20, "nrs_impact": 0.10, "top_node": "youtube.com"},
        "official_mall_guarantee": {"sov_impact": 0.10, "nrs_impact": 0.35, "top_node": "shopee.co.th"},
        "flash_sale_pricing": {"sov_impact": 0.25, "nrs_impact": -0.05, "top_node": "lazada.co.th"},
        "structured_schema_markup": {"sov_impact": 0.18, "nrs_impact": 0.15, "top_node": "brand.co.th"},
    }

    @classmethod
    def simulate_strategy(
        cls, target_brand: str, current_sov_pct: float, current_nrs: float, strategy_levers: list[str]
    ) -> dict[str, Any]:
        """Forecasts SoV and NRS change based on selected strategic intervention levers."""
        delta_sov = 0.0
        delta_nrs = 0.0
        activated_nodes = []

        for lever in strategy_levers:
            cfg = cls.LEVER_WEIGHTS.get(lever)
            if cfg:
                delta_sov += cfg["sov_impact"] * 100
                delta_nrs += cfg["nrs_impact"] * 100
                activated_nodes.append(cfg["top_node"])

        projected_sov = min(100.0, round(current_sov_pct + delta_sov, 1))
        projected_nrs = min(100.0, max(-100.0, round(current_nrs + delta_nrs, 1)))

        return {
            "target_brand": target_brand,
            "baseline": {"share_of_voice_pct": current_sov_pct, "net_recommendation_score": current_nrs},
            "simulated": {"share_of_voice_pct": projected_sov, "net_recommendation_score": projected_nrs},
            "impact_delta": {
                "sov_gain_pct": round(projected_sov - current_sov_pct, 1),
                "nrs_gain_points": round(projected_nrs - current_nrs, 1),
            },
            "activated_citation_nodes": list(set(activated_nodes)),
            "feasibility_score": round(max(0.6, 1.0 - (len(strategy_levers) * 0.08)), 2),
            "executive_recommendation": f"ดำเนินกลยุทธ์ {', '.join(strategy_levers)} เพื่อเพิ่ม AI Visibility ได้ถึง +{round(projected_sov - current_sov_pct, 1)}% และความน่าเชื่อถือ +{round(projected_nrs - current_nrs, 1)} คะแนน",
        }
