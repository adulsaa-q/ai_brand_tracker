import hashlib
import random
import time
from datetime import datetime

from src.engines.base import BaseObservationEngine
from src.ids import new_observation_id
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


def _stable_seed(*parts: str) -> int:
    """Process-independent seed.

    Phase 0 remediation: the mock engine seeded ``random`` with the builtin
    ``hash()`` of the query text, which is salted per process (PYTHONHASHSEED),
    so "deterministic sandbox" was not deterministic across runs. SHA-256 gives
    the same value every process.
    """
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


class MockObservationEngine(BaseObservationEngine):
    """Deterministic synthetic engine. Output is clearly labelled ``synthetic``
    and must never be presented to a user as live data."""

    def __init__(self, model_name: str = "mock-synthetic-v1", api_key: str | None = None):
        super().__init__(model_name=model_name, api_key=api_key)

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        start_time = time.time()
        rng = random.Random(_stable_seed(query_text, ",".join(sorted(target_brands))))

        k = rng.randint(2, min(4, len(target_brands))) if len(target_brands) >= 2 else len(target_brands)
        selected_brands = rng.sample(target_brands, k=k)
        mentions = []

        for rank, b in enumerate(selected_brands, start=1):
            sentiment = rng.choice(["positive", "positive", "neutral", "negative"])
            intent = rng.choice(["strongly_recommended", "recommended", "neutral_mention"])
            mentions.append(
                BrandMentionDetail(
                    brand_id=b.lower().replace(" ", "_"),
                    brand_name=b,
                    mentioned=True,
                    rank=rank,
                    recommendation_intent=intent,
                    sentiment=sentiment,
                    key_strengths_mentioned=["โปรโมชั่นดี", "สินค้าแท้ 100%", "ส่งรวดเร็ว"]
                    if sentiment == "positive"
                    else ["สินค้าหมดบ่อย"],
                    key_weaknesses_mentioned=["ค่าส่งแพง"] if sentiment == "negative" else [],
                )
            )

        citations = [
            CitationSource(domain="pantip.com", title="กระทู้รีวิวสกินแคร์", source_type="forum"),
            CitationSource(domain="sanook.com", title="รวมโปรโมชั่น Double Day", source_type="news"),
            CitationSource(domain="shopee.co.th", title="Shopee Mall Official", source_type="marketplace"),
        ]

        latency = int((time.time() - start_time) * 1000) + rng.randint(200, 800)

        return RawObservation(
            observation_id=new_observation_id("mock"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="mock",
            model_name=self.model_name or "mock-synthetic-v1",
            answer_surface="synthetic",
            grounding_enabled=False,
            response_raw_text=f"[SYNTHETIC] สรุปคำแนะนำสำหรับ: {query_text}",
            response_latency_ms=latency,
            token_count=rng.randint(350, 850),
            parse_status="not_applicable",
            brand_mentions=mentions,
            citations=citations,
        )
