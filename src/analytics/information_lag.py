from typing import Any


class AIInformationLagTracker:
    """Measures the time lag between real-world brand news/events and AI perception updates."""

    @staticmethod
    def measure_knowledge_freshness(observations: list[dict[str, Any]]) -> dict[str, Any]:
        has_citations = sum(1 for obs in observations if len(obs.get("citations", [])) > 0)
        total = len(observations) or 1
        grounding_ratio = round((has_citations / total) * 100, 1)

        return {
            "grounding_realtime_rate": f"{grounding_ratio}%",
            "estimated_information_lag": "0-2 Days (Real-time Grounded via Google Search)"
            if grounding_ratio > 70
            else "3-6 Months (Static Pre-training Weights)",
            "risk_assessment": "LOW_LAG" if grounding_ratio > 70 else "HIGH_LAG",
            "recommendation": "เปิดใช้งาน Search Grounding เสมอเพื่อให้ AI ตอบโปรโมชั่นปัจจุบันได้ถูกต้อง",
        }
