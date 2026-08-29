import json
import os
import time
from datetime import datetime

from src.engines.base import BaseObservationEngine
from src.models.observations import BrandMentionDetail, RawObservation


class OpenRouterEngine(BaseObservationEngine):
    def __init__(self, model_name: str = "deepseek/deepseek-chat:free", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("OPENROUTER_API_KEY"))

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        if not self.api_key:
            raise RuntimeError("OpenRouter API Key not configured. Set OPENROUTER_API_KEY.")

        import urllib.request
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/adulsaa-q/ai_brand_tracker",
            "X-Title": "Thailand AI Market Intelligence",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are an expert Thai Market Intelligence Analyst. Always return JSON in ```json ... ```."},
                {"role": "user", "content": f'Consumer Query: "{query_text}"\nTarget Brands: {", ".join(target_brands)}\n\nReturn JSON with brand_mentions array.'}
            ],
            "temperature": 0.2
        }

        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        latency = int((time.time() - start_time) * 1000)
        raw_text = data["choices"][0]["message"]["content"]

        mentions = []
        try:
            if "```json" in raw_text:
                json_str = raw_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
            parsed = json.loads(json_str)
            for m in parsed.get("brand_mentions", []):
                mentions.append(BrandMentionDetail(
                    brand_id=m["brand_name"].lower().replace(" ", "_"),
                    brand_name=m["brand_name"],
                    mentioned=m.get("mentioned", True),
                    rank=m.get("rank"),
                    recommendation_intent=m.get("recommendation_intent", "recommended"),
                    sentiment=m.get("sentiment", "neutral"),
                    key_strengths_mentioned=m.get("key_strengths", []),
                    key_weaknesses_mentioned=m.get("key_weaknesses", [])
                ))
        except Exception:
            pass

        return RawObservation(
            observation_id=f"obs_or_{int(time.time())}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            engine_provider="openrouter",
            model_name=self.model_name,
            grounding_enabled=False,
            response_raw_text=raw_text,
            response_latency_ms=latency,
            brand_mentions=mentions,
            citations=[]
        )
