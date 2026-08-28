from typing import List, Dict, Any

class OpportunityFinder:
    @staticmethod
    def identify_gaps(focal_brand: str, metrics: Dict[str, Any], query_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        opportunities = []
        missed_queries = []
        for q in query_results:
            focal_present = any(m["brand_name"].lower() == focal_brand.lower() for m in q.get("brand_mentions", []))
            comp_top = [m["brand_name"] for m in q.get("brand_mentions", []) if m.get("rank") == 1]
            if not focal_present and comp_top:
                missed_queries.append({
                    "query_text": q["query_text"],
                    "winner": comp_top[0],
                    "category": q.get("category", "General")
                })

        if missed_queries:
            opportunities.append({
                "type": "VISIBILITY_GAP",
                "severity": "HIGH",
                "title": f"แบรนด์ขาดการมองเห็นใน {len(missed_queries)} คำถามสำคัญ",
                "impact": f"คู่แข่ง ({', '.join(set(m['winner'] for m in missed_queries[:3]))}) ชิงอันดับ 1 ไปได้",
                "recommended_action": "สร้าง Content SEO / แคมเปญ Grounding เพื่อดันแบรนด์ให้ติดอันดับในคำถามกลุ่มนี้",
                "sample_queries": [m["query_text"] for m in missed_queries[:3]]
            })

        return opportunities
