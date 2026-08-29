import random
import time
from datetime import datetime

from src.engines.base import BaseObservationEngine
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


class MockObservationEngine(BaseObservationEngine):
    def __init__(self, model_name: str = "gemini-2.5-flash-mock", api_key: str | None = None):
        super().__init__(model_name=model_name, api_key=api_key)

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        start_time = time.time()
        rng = random.Random(hash(query_text) % 10000)
        
        selected_brands = rng.sample(target_brands, k=rng.randint(2, min(4, len(target_brands))))
        mentions = []
        
        for rank, b in enumerate(selected_brands, start=1):
            sentiment = rng.choice(["positive", "positive", "neutral", "negative"])
            intent = rng.choice(["strongly_recommended", "recommended", "neutral_mention"])
            
            mentions.append(BrandMentionDetail(
                brand_id=b.lower().replace(" ", "_"),
                brand_name=b,
                mentioned=True,
                rank=rank,
                recommendation_intent=intent,
                sentiment=sentiment,
                key_strengths_mentioned=["โปรโมชั่นดี", "สินค้าแท้ 100%", "ส่งรวดเร็ว"] if sentiment == "positive" else ["สินค้าหมดบ่อย"],
                key_weaknesses_mentioned=["ค่าส่งแพง"] if sentiment == "negative" else []
            ))
            
        citations = [
            CitationSource(domain="pantip.com", title="กระทู้รีวิวสกินแคร์", source_type="forum"),
            CitationSource(domain="sanook.com", title="รวมโปรโมชั่น Double Day", source_type="news"),
            CitationSource(domain="shopee.co.th", title="Shopee Mall Official", source_type="marketplace")
        ]
        
        latency = int((time.time() - start_time) * 1000) + rng.randint(200, 800)
        
        return RawObservation(
            observation_id=f"obs_mock_{int(time.time())}_{rng.randint(100, 999)}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            engine_provider="google_gemini",
            model_name=self.model_name or "gemini-2.5-flash-mock",
            grounding_enabled=True,
            response_raw_text=f"สรุปคำแนะนำสำหรับ: {query_text}",
            response_latency_ms=latency,
            token_count=rng.randint(350, 850),
            brand_mentions=mentions,
            citations=citations
        )
