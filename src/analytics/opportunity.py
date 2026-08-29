# src/analytics/opportunity.py
from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.brands import BrandIdentity


def _as_identity(focal: BrandIdentity | str) -> BrandIdentity:
    if isinstance(focal, BrandIdentity):
        return focal
    return BrandIdentity(brand_id=str(focal), name=str(focal))


class OpportunityFinder:
    @staticmethod
    def identify_gaps(
        focal: BrandIdentity | str,
        metrics: dict[str, Any],
        query_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        focal_identity = _as_identity(focal)
        opportunities = []
        missed_by_category = defaultdict(list)

        for q in query_results:
            mentions = q.get("brand_mentions", [])
            focal_present = any(
                focal_identity.matches(m.get("brand_name", "")) and m.get("mentioned", True) for m in mentions
            )
            comp_top = [
                m["brand_name"]
                for m in mentions
                if m.get("rank") == 1 and not focal_identity.matches(m.get("brand_name", ""))
            ]
            cat = q.get("category", "General")

            if not focal_present and comp_top:
                missed_by_category[cat].append({"query_text": q.get("query_text", ""), "winner": comp_top[0]})

        if not missed_by_category:
            top_brands = metrics.get("brands", [])
            leader = top_brands[0]["brand"] if top_brands else focal_identity.name
            opportunities.append(
                {
                    "id": "opp_01",
                    "type": "CATEGORY_VISIBILITY_GAP",
                    "priority": "P1 (HIGH IMPACT / LOW EFFORT)",
                    "severity": "HIGH",
                    "category": "Brand Authority & Schema Grounding",
                    "title": f"การป้องกันส่วนแบ่งตลาดและการขยายการรับรู้เหนือ {leader}",
                    "what_is_happening": f"แบรนด์คู่แข่งและผู้นำตลาด ({leader}) ดึงดูดการตอบสนองของ AI อย่างต่อเนื่องในกลุ่มคำถามเชิงพาณิชย์",
                    "why_it_is_happening": "AI ดึงข้อมูลจาก Marketplace Mall และ Content Hub ที่มี Structured Entity และ FAQ ชัดเจน",
                    "so_what": "สูญเสียการเข้าถึงกลุ่มลูกค้าที่มีกำลังซื้อสูงและค้นหาข้อมูลผ่าน Generative Search",
                    "now_what": "สร้าง Structured Schema Markup และขยายการเผยแพร่ข้อมูลผ่าน Creator Video Proof (YouTube Shorts/Lemon8)",
                    "expected_impact": "ต้องประเมินจากผลการตรวจวัดจริงหลายรอบ",
                    "effort": "LOW (2-3 สัปดาห์)",
                    "confidence": "LOW (ยังไม่พบช่องว่างที่ชัดเจนในชุดข้อมูลนี้)",
                }
            )
            return opportunities

        for idx, (cat, items) in enumerate(missed_by_category.items()):
            winners = list(dict.fromkeys(i["winner"] for i in items))
            severity = "HIGH" if len(items) >= 2 else "MEDIUM"
            priority = "P1 (HIGH IMPACT / LOW EFFORT)" if severity == "HIGH" else "P2 (MEDIUM IMPACT)"

            opportunities.append(
                {
                    "id": f"opp_{idx + 1:02d}",
                    "type": "CATEGORY_VISIBILITY_GAP",
                    "priority": priority,
                    "severity": severity,
                    "category": cat,
                    "title": f"แบรนด์เสียโอกาสการแนะนำในหมวด {cat} ({len(items)} คำถาม)",
                    "what_is_happening": f"จากการตรวจวัด {len(items)} คำถามในหมวดนี้ แบรนด์ {focal_identity.name} ไม่ถูกกล่าวถึงในคำตอบของ AI",
                    "why_it_is_happening": f"คู่แข่งหลัก ({', '.join(winners[:2])}) ผูกขาดแหล่งอ้างอิงและเนื้อหาใน Category นี้",
                    "so_what": "ลูกค้าที่ค้นหาข้อมูลเปรียบเทียบในหมวดนี้จะถูกชักจูงไปยังคู่แข่งโดยตรง",
                    "now_what": f"กระจาย Digital Footprint และสร้างคอนเทนต์ตอบโจทย์คำถาม {cat} ลงในแพลตฟอร์มคอมมูนิตี้และเว็บบอร์ด",
                    "missed_query_count": len(items),
                    "effort": "MEDIUM (3-4 สัปดาห์)",
                    "confidence": "MEDIUM (อ้างอิงจากจำนวนคำถามที่ตรวจพบในรอบนี้)",
                    "sample_queries": [i["query_text"] for i in items[:2]],
                }
            )

        return opportunities
