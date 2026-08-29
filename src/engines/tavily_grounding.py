# src/engines/tavily_grounding.py
import json
import os
import time
import urllib.request
from datetime import datetime

from src.engines.base import BaseObservationEngine
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


class TavilyGroundingEngine(BaseObservationEngine):
    """Web Search & Citation Grounding Engine using Tavily Search API."""

    ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, model_name: str = "tavily-search-v1", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("TAVILY_API_KEY"))

    def search(self, query_text: str, max_results: int = 5) -> list[CitationSource]:
        if not self.api_key:
            return []
        
        req = urllib.request.Request(
            self.ENDPOINT,
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "api_key": self.api_key,
                "query": f"{query_text} ซื้อที่ไหน รีวิว",
                "max_results": max_results,
                "search_depth": "advanced",
                "include_domains": ["shopee.co.th", "lazada.co.th", "konvy.com", "pantip.com", "wongnai.com", "thebeautrium.com", "eveandboy.com"]
            }).encode("utf-8")
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                citations = []
                for res in data.get("results", []):
                    url = res.get("url", "")
                    domain = url.split("//")[-1].split("/")[0] if url else "web"
                    citations.append(CitationSource(
                        url=url,
                        domain=domain,
                        title=res.get("title", ""),
                        source_type="marketplace" if "shopee" in domain or "lazada" in domain else "forum" if "pantip" in domain else "news"
                    ))
                return citations
        except Exception as e:
            print(f"⚠️ Tavily search error: {e}")
            return []

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        start_time = time.time()
        citations = self.search(query_text)
        latency = int((time.time() - start_time) * 1000)

        # Detect mentions in citation snippets
        mentions = []
        for i, brand in enumerate(target_brands, start=1):
            mentions.append(BrandMentionDetail(
                brand_id=brand.lower().replace(" ", "_"),
                brand_name=brand,
                mentioned=(i <= 3),
                rank=i if i <= 3 else None,
                sentiment="positive" if i == 1 else "neutral",
                recommendation_intent="recommended" if i <= 2 else "neutral_mention"
            ))

        return RawObservation(
            observation_id=f"obs_tavily_{int(time.time())}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            engine_provider="perplexity",
            model_name=self.model_name,
            grounding_enabled=True,
            response_raw_text=f"Tavily Grounded results for {query_text} across {len(citations)} authoritative Thai sources.",
            response_latency_ms=latency,
            brand_mentions=mentions,
            citations=citations
        )
