# src/engines/serper_engine.py
import os
import time
from datetime import datetime

from src.engines._http import request_json
from src.engines.base import BaseObservationEngine, match_terms
from src.exceptions import EngineError
from src.ids import new_observation_id
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


class SerperGoogleEngine(BaseObservationEngine):
    """Google organic SERP ranking via Serper.dev.

    ``organic_serp`` surface: ``rank`` is a search-result position, NOT a
    generative recommendation rank. Analytics must not average it against
    generative-answer ranks.
    """

    ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, model_name: str = "google-serp-th", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("SERPER_API_KEY"))

    def observe(
        self,
        query_id: str,
        query_text: str,
        target_brands: list[str],
        brand_aliases: dict[str, list[str]] | None = None,
    ) -> RawObservation:
        if not self.api_key:
            raise EngineError("Serper engine requires SERPER_API_KEY", {"engine": "serper"})

        start_time = time.time()
        data, retries = request_json(
            self.ENDPOINT,
            payload={"q": query_text, "gl": "th", "hl": "th", "num": 10},
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            timeout=15,
            engine="serper",
        )
        latency = int((time.time() - start_time) * 1000)
        organic_results = data.get("organic", [])

        citations: list[CitationSource] = []
        brand_positions: dict[str, int] = {}
        for idx, item in enumerate(organic_results, start=1):
            link = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            domain = link.split("//")[-1].split("/")[0] if link else "google"
            citations.append(
                CitationSource(
                    url=link,
                    domain=domain,
                    title=title,
                    source_type="marketplace" if ("shopee" in domain or "lazada" in domain) else "news",
                )
            )
            full_text = f"{title} {snippet}".lower()
            for brand in target_brands:
                if brand in brand_positions:
                    continue
                if any(term in full_text for term in match_terms(brand, brand_aliases)):
                    brand_positions[brand] = idx

        mentions = [
            BrandMentionDetail(
                brand_id=brand.lower().replace(" ", "_"),
                brand_name=brand,
                mentioned=brand in brand_positions,
                rank=brand_positions.get(brand),
                sentiment="neutral",
                recommendation_intent="neutral_mention",
            )
            for brand in target_brands
        ]

        return RawObservation(
            observation_id=new_observation_id("serper"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="serper",
            model_name=self.model_name,
            answer_surface="organic_serp",
            grounding_enabled=True,
            retry_count=retries,
            response_raw_text=f"Google SERP for: {query_text} ({len(organic_results)} organic results)",
            response_latency_ms=latency,
            parse_status="not_applicable",
            brand_mentions=mentions,
            citations=citations,
        )
