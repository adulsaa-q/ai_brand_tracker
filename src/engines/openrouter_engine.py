import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

from src.engines._parsing import parse_brand_mentions
from src.engines.base import BaseObservationEngine
from src.exceptions import EngineError, RateLimitExceededError
from src.ids import new_observation_id
from src.models.observations import RawObservation

_PROMPT_VERSION = "openrouter.brand_audit.v1"
_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterEngine(BaseObservationEngine):
    prompt_version = _PROMPT_VERSION

    def __init__(self, model_name: str = "deepseek/deepseek-chat:free", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("OPENROUTER_API_KEY"))

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        if not self.api_key:
            raise EngineError("OpenRouter engine requires OPENROUTER_API_KEY", {"engine": "openrouter"})

        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/adulsaa-q/ai_brand_tracker",
            "X-Title": "Thailand AI Market Intelligence",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert Thai Market Intelligence Analyst. Always return JSON in ```json ... ```.",
                },
                {
                    "role": "user",
                    "content": (
                        f'Consumer Query: "{query_text}"\n'
                        f"Target Brands: {', '.join(target_brands)}\n\n"
                        "Return JSON with a brand_mentions array "
                        "(brand_name, mentioned, rank, recommendation_intent, sentiment, key_strengths, key_weaknesses)."
                    ),
                },
            ],
            "temperature": 0.2,
        }

        req = urllib.request.Request(_ENDPOINT, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise RateLimitExceededError(
                    "OpenRouter rate limit", {"engine": "openrouter", "model": self.model_name}
                ) from exc
            raise EngineError(f"OpenRouter HTTP {exc.code}", {"engine": "openrouter", "query_id": query_id}) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EngineError(f"OpenRouter call failed: {exc}", {"engine": "openrouter", "query_id": query_id}) from exc

        latency = int((time.time() - start_time) * 1000)
        try:
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EngineError(
                f"OpenRouter response shape unexpected: {exc}", {"engine": "openrouter", "query_id": query_id}
            ) from exc

        mentions, parse_status = parse_brand_mentions(raw_text, query_id=query_id)
        usage = data.get("usage") or {}

        return RawObservation(
            observation_id=new_observation_id("openrouter"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="openrouter",
            model_name=self.model_name,
            answer_surface="generative_answer",
            grounding_enabled=False,
            response_raw_text=raw_text,
            response_latency_ms=latency,
            token_count=usage.get("total_tokens"),
            parse_status=parse_status,
            brand_mentions=mentions,
            citations=[],
        )
