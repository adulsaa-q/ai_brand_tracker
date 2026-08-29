from typing import Any


class AIInformationLagTracker:
    """Reports how grounded a scan's answers were.

    Phase 0 remediation: this used to emit a fabricated "0-2 Days (Real-time)"
    vs "3-6 Months (Static)" verdict purely from whether the citations list was
    non-empty. A real information-lag measurement requires comparing cited
    content dates against known real-world events and is deferred. We now only
    report the grounding rate, which is an actual measurement.
    """

    @staticmethod
    def measure_knowledge_freshness(observations: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(observations)
        if total == 0:
            return {"grounded_rate_pct": 0.0, "grounded_observations": 0, "total_observations": 0, "note": "no data"}

        grounded = sum(1 for obs in observations if len(obs.get("citations", [])) > 0)
        rate = round((grounded / total) * 100, 1)

        return {
            "grounded_rate_pct": rate,
            "grounded_observations": grounded,
            "total_observations": total,
            "note": (
                "Fraction of observations that carried at least one citation. "
                "Not a time-lag estimate - a dated-content vs event-date comparison is not yet implemented."
            ),
            "recommendation": "เปิด Search Grounding ทุกครั้งเพื่อให้ AI อ้างอิงโปรโมชั่น/ข้อมูลปัจจุบัน",
        }
