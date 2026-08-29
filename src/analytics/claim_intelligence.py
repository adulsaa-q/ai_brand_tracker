from typing import List, Dict, Any

class ClaimIntelligenceEngine:
    """Audits factual claims made by AI about brands to detect outdated info, policy conditions, or hallucinations."""

    CLAIM_RULES = [
        {"keyword": "ส่งฟรี", "verdict": "CONDITIONAL", "note": "ต้องใช้โค้ดส่งฟรีขั้นต่ำตามแคมเปญ ไม่ใช่ส่งฟรีอัตโนมัติทุกออเดอร์"},
        {"keyword": "แท้", "verdict": "VERIFIED_OFFICIAL", "note": "การันตีเฉพาะร้านค้า Official Mall / LazMall / Counter เท่านั้น"},
        {"keyword": "same day", "verdict": "GEOGRAPHIC_LIMITED", "note": "รองรับเฉพาะพื้นที่กรุงเทพฯ และปริมณฑลตามรอบเวลา"},
        {"keyword": "คืนเงิน", "verdict": "POLICY_CONDITIONAL", "note": "มีเงื่อนไขระยะเวลา 7-15 วัน และสภาพสินค้าต้องสมบูรณ์"}
    ]

    @classmethod
    def audit_claims(cls, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        claim_alerts = []
        seen_claims = set()

        for obs in observations:
            for m in obs.get("brand_mentions", []):
                b_name = m.get("brand_name", "")
                claims = m.get("key_strengths_mentioned", []) + m.get("price_or_deal_claims", [])

                for c in claims:
                    c_lower = c.lower()
                    for rule in cls.CLAIM_RULES:
                        if rule["keyword"].lower() in c_lower:
                            claim_key = f"{b_name}_{rule['keyword']}"
                            if claim_key not in seen_claims:
                                seen_claims.add(claim_key)
                                claim_alerts.append({
                                    "brand": b_name,
                                    "claim_type": "MARKETING_POLICY",
                                    "extracted_claim": c,
                                    "audit_verdict": rule["verdict"],
                                    "note": rule["note"],
                                    "query_id": obs.get("query_id")
                                })

        return claim_alerts
