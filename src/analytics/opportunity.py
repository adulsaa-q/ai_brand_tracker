from collections import defaultdict
from typing import Any


class OpportunityFinder:
    @staticmethod
    def identify_gaps(
        focal_brand: str, metrics: dict[str, Any], query_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        opportunities = []
        missed_by_category = defaultdict(list)

        for q in query_results:
            mentions = q.get("brand_mentions", [])
            focal_present = any(
                m["brand_name"].lower() == focal_brand.lower() and m.get("mentioned", True) for m in mentions
            )
            comp_top = [m["brand_name"] for m in mentions if m.get("rank") == 1]
            cat = q.get("category", "General")

            if not focal_present and comp_top:
                missed_by_category[cat].append({"query_text": q["query_text"], "winner": comp_top[0]})

        for cat, items in missed_by_category.items():
            winners = list(set(i["winner"] for i in items))
            opportunities.append(
                {
                    "type": "CATEGORY_VISIBILITY_GAP",
                    "severity": "HIGH" if len(items) >= 2 else "MEDIUM",
                    "category": cat,
                    "title": f"แบรนด์เสียส่วนแบ่งในหมวด {cat} ({len(items)} คำถาม)",
                    "impact": f"คู่แข่งหลัก ({', '.join(winners[:2])}) ผูกขาดการเป็น Top Recommendation",
                    "evidence": f"จากการตรวจวัด {len(items)} คำถามในหมวดนี้ แบรนด์ไม่ถูกกล่าวถึง",
                    "recommended_action": f"สร้าง Content Hub และกระจาย Authority Signals เจาะกลุ่มคำถาม {cat}",
                    "priority": "P1 (HIGH IMPACT / LOW EFFORT)",
                    "sample_queries": [i["query_text"] for i in items[:2]],
                }
            )

        return opportunities
