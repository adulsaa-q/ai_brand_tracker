# src/engines/tavily_grounding.py
import os
import time
from datetime import datetime

from src.engines._http import request_json
from src.engines.base import BaseObservationEngine, match_terms
from src.exceptions import EngineError
from src.ids import new_observation_id
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


class TavilyGroundingEngine(BaseObservationEngine):
    """Web retrieval / citation grounding via Tavily.

    ``web_retrieval`` surface: returns documents, not a ranked recommendation.
    A brand "mention" here means the brand name appeared in a retrieved
    document's title or content - there is no rank and no sentiment.
    """

    ENDPOINT = "https://api.tavily.com/search"
    _DOMAINS = [
        "shopee.co.th",
        "lazada.co.th",
        "konvy.com",
        "pantip.com",
        "wongnai.com",
        "thebeautrium.com",
        "eveandboy.com",
    ]

    def __init__(self, model_name: str = "tavily-search-v1", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("TAVILY_API_KEY"))

    def observe(
        self,
        query_id: str,
        query_text: str,
        target_brands: list[str],
        brand_aliases: dict[str, list[str]] | None = None,
    ) -> RawObservation:
        if not self.api_key:
            raise EngineError("Tavily engine requires TAVILY_API_KEY", {"engine": "tavily"})

        start_time = time.time()
        data, retries = request_json(
            self.ENDPOINT,
            payload={
                "api_key": self.api_key,
                "query": f"{query_text} ซื้อที่ไหน รีวิว",
                "max_results": 5,
                "search_depth": "basic",  # 1 credit vs 2 for "advanced"; keeps the free tier lasting
                "include_domains": self._DOMAINS,
            },
            headers={"Content-Type": "application/json"},
            timeout=25,
            engine="tavily",
        )
        latency = int((time.time() - start_time) * 1000)
        results = data.get("results", [])

        citations: list[CitationSource] = []
        corpus_parts: list[str] = []
        for res in results:
            url = res.get("url", "")
            domain = url.split("//")[-1].split("/")[0] if url else "web"
            title = res.get("title", "")
            corpus_parts.append(f"{title} {res.get('content', '')}".lower())
            citations.append(
                CitationSource(
                    url=url,
                    domain=domain,
                    title=title,
                    source_type="marketplace"
                    if ("shopee" in domain or "lazada" in domain)
                    else "forum"
                    if "pantip" in domain
                    else "news",
                )
            )
        corpus = " ".join(corpus_parts)

        mentions = [
            BrandMentionDetail(
                brand_id=brand.lower().replace(" ", "_"),
                brand_name=brand,
                mentioned=any(term in corpus for term in match_terms(brand, brand_aliases)),
                rank=None,
                sentiment="neutral",
                recommendation_intent="neutral_mention",
            )
            for brand in target_brands
        ]

        return RawObservation(
            observation_id=new_observation_id("tavily"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="tavily",
            model_name=self.model_name,
            answer_surface="web_retrieval",
            grounding_enabled=True,
            retry_count=retries,
            response_raw_text=f"Tavily retrieved {len(citations)} Thai sources for: {query_text}",
            response_latency_ms=latency,
            parse_status="not_applicable",
            brand_mentions=mentions,
            citations=citations,
        )
