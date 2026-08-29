# src/engines/tavily_grounding.py
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

from src.engines.base import BaseObservationEngine
from src.exceptions import EngineError, RateLimitExceededError
from src.ids import new_observation_id
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


class TavilyGroundingEngine(BaseObservationEngine):
    """Web retrieval / citation grounding via Tavily.

    This is a ``web_retrieval`` surface: it returns documents, not a ranked
    recommendation. Brand "mentions" here mean the brand name appeared in a
    retrieved document's title or content - there is no rank and no sentiment.
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

    def _search(self, query_text: str, max_results: int = 5) -> list[dict]:
        req = urllib.request.Request(
            self.ENDPOINT,
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "api_key": self.api_key,
                    "query": f"{query_text} ซื้อที่ไหน รีวิว",
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_domains": self._DOMAINS,
                }
            ).encode("utf-8"),
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8")).get("results", [])
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RateLimitExceededError("Tavily rate limit", {"engine": "tavily"}) from exc
            raise EngineError(f"Tavily HTTP {exc.code}", {"engine": "tavily"}) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EngineError(f"Tavily call failed: {exc}", {"engine": "tavily"}) from exc

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        if not self.api_key:
            raise EngineError("Tavily engine requires TAVILY_API_KEY", {"engine": "tavily"})

        start_time = time.time()
        results = self._search(query_text)
        latency = int((time.time() - start_time) * 1000)

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
                mentioned=brand.lower() in corpus,
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
            response_raw_text=f"Tavily retrieved {len(citations)} Thai sources for: {query_text}",
            response_latency_ms=latency,
            parse_status="not_applicable",
            brand_mentions=mentions,
            citations=citations,
        )
