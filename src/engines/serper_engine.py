# src/engines/serper_engine.py
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


class SerperGoogleEngine(BaseObservationEngine):
    """Google organic SERP ranking via Serper.dev.

    This is an ``organic_serp`` surface: ``rank`` is a search-result position,
    NOT a generative recommendation rank. Analytics must not average it against
    generative-answer ranks.
    """

    ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, model_name: str = "google-serp-th", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("SERPER_API_KEY"))

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        if not self.api_key:
            raise EngineError("Serper engine requires SERPER_API_KEY", {"engine": "serper"})

        start_time = time.time()
        req = urllib.request.Request(
            self.ENDPOINT,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            data=json.dumps({"q": query_text, "gl": "th", "hl": "th", "num": 10}).encode("utf-8"),
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RateLimitExceededError("Serper rate limit", {"engine": "serper"}) from exc
            raise EngineError(f"Serper HTTP {exc.code}", {"engine": "serper", "query_id": query_id}) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EngineError(f"Serper call failed: {exc}", {"engine": "serper", "query_id": query_id}) from exc

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
                if brand.lower() in full_text and brand not in brand_positions:
                    brand_positions[brand] = idx

        mentions = []
        for brand in target_brands:
            rank = brand_positions.get(brand)
            mentions.append(
                BrandMentionDetail(
                    brand_id=brand.lower().replace(" ", "_"),
                    brand_name=brand,
                    mentioned=rank is not None,
                    rank=rank,
                    sentiment="neutral",
                    recommendation_intent="neutral_mention",
                )
            )

        return RawObservation(
            observation_id=new_observation_id("serper"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="serper",
            model_name=self.model_name,
            answer_surface="organic_serp",
            grounding_enabled=True,
            response_raw_text=(f"Google SERP for Thai query: {query_text} ({len(organic_results)} organic results)"),
            response_latency_ms=latency,
            parse_status="not_applicable",
            brand_mentions=mentions,
            citations=citations,
        )
