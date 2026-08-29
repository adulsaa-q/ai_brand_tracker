import os
import time
from datetime import datetime

from src.engines._http import request_json
from src.engines._parsing import parse_brand_mentions
from src.engines.base import BaseObservationEngine
from src.exceptions import EngineError
from src.ids import new_observation_id
from src.models.observations import RawObservation
from src.prompts import get_prompt

_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterEngine(BaseObservationEngine):
    def __init__(self, model_name: str = "deepseek/deepseek-chat:free", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("OPENROUTER_API_KEY"))
        self._system = get_prompt("openrouter.system")
        self._user = get_prompt("openrouter.brand_audit")

    def observe(
        self,
        query_id: str,
        query_text: str,
        target_brands: list[str],
        brand_aliases: dict[str, list[str]] | None = None,
    ) -> RawObservation:
        if not self.api_key:
            raise EngineError("OpenRouter engine requires OPENROUTER_API_KEY", {"engine": "openrouter"})

        start_time = time.time()
        brands = "; ".join(
            f"{n} ({', '.join(a for a in (brand_aliases or {}).get(n, []) if a.lower() != n.lower())})"
            if (brand_aliases or {}).get(n)
            else n
            for n in target_brands
        )
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self._system.template},
                {"role": "user", "content": self._user.render(query_text=query_text, brands=brands)},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/adulsaa-q/ai_brand_tracker",
            "X-Title": "Thailand AI Market Intelligence",
            "Content-Type": "application/json",
        }

        data, retries = request_json(_ENDPOINT, payload=payload, headers=headers, timeout=60, engine="openrouter")
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
            prompt_version=self._user.id,
            retry_count=retries,
            response_raw_text=raw_text,
            response_latency_ms=latency,
            token_count=usage.get("total_tokens"),
            parse_status=parse_status,
            brand_mentions=mentions,
            citations=[],
        )
