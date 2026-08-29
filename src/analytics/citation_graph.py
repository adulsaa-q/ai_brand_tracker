from collections import defaultdict
from typing import Any


class CitationInfluenceAnalyzer:
    """Analyzes which web domains and content sources exert the highest influence on AI answers."""

    DOMAIN_CATEGORIES = {
        "pantip.com": "Webboard / Forum (High Trust)",
        "wongnai.com": "Beauty & Lifestyle Reviews",
        "sanook.com": "News & Lifestyle Portal",
        "kapook.com": "News & Trends Portal",
        "shopee.co.th": "Direct Marketplace Mall",
        "lazada.co.th": "Direct Marketplace Mall",
        "konvy.com": "Specialized Retailer Official",
        "thebeautrium.com": "Specialized Retailer Official",
        "eveandboy.com": "Specialized Retailer Official",
        "cosmenet.in.th": "Dedicated Beauty Review Community",
        "lemon8-app.com": "Short-form Lifestyle Reviews",
        "thairath.co.th": "Mainstream News",
        "khaosod.co.th": "Mainstream News"
    }

    @classmethod
    def analyze_influence(cls, observations: list[dict[str, Any]]) -> dict[str, Any]:
        domain_counts = defaultdict(int)
        domain_brand_correlations = defaultdict(lambda: defaultdict(int))
        
        for obs in observations:
            citations = obs.get("citations", [])
            mentions = [m["brand_name"] for m in obs.get("brand_mentions", []) if m.get("mentioned", True)]
            
            for c in citations:
                d = c.get("domain", "").lower().replace("www.", "")
                if not d:
                    continue
                domain_counts[d] += 1
                for b in mentions:
                    domain_brand_correlations[d][b] += 1

        total_citations = sum(domain_counts.values()) or 1
        rankings = []
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            category = cls.DOMAIN_CATEGORIES.get(domain, "Other Web Source")
            share_pct = round((count / total_citations) * 100, 1)
            top_associated_brands = sorted(domain_brand_correlations[domain].items(), key=lambda x: x[1], reverse=True)
            
            rankings.append({
                "domain": domain,
                "category": category,
                "citation_count": count,
                "influence_share_pct": share_pct,
                "top_associated_brand": top_associated_brands[0][0] if top_associated_brands else "N/A"
            })

        return {
            "total_citations": total_citations,
            "unique_domains": len(domain_counts),
            "domain_rankings": rankings
        }
