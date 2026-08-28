from typing import List, Dict, Any

class ClaimIntelligenceEngine:
    """Audits factual claims made by AI about brands to detect outdated info or hallucinations."""

    @classmethod
    def audit_claims(cls, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        claim_alerts = []
        for obs in observations:
            for m in obs.get("brand_mentions", []):
                b_name = m["brand_name"].lower()
                strengths = m.get("key_strengths_mentioned", [])
                
                if "shopee" in b_name:
                    for s in strengths:
                        if "ส่งฟรี" in s:
                            claim_alerts.append({
                                "brand": "Shopee Thailand",
                                "claim_type": "PROMOTION_POLICY",
                                "extracted_claim": s,
                                "audit_verdict": "CONDITIONAL",
                                "note": "ต้องใช้โค้ดส่งฟรีเฉพาะช่วงแคมเปญ ไม่ใช่ส่งฟรีอัตโนมัติทุกร้าน",
                                "query_id": obs.get("query_id")
                            })
        return claim_alerts
