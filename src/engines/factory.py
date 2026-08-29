from __future__ import annotations

from typing import Literal

from src.engines.base import BaseObservationEngine
from src.engines.gemini_engine import GeminiObservationEngine
from src.engines.mock_engine import MockObservationEngine
from src.engines.openrouter_engine import OpenRouterEngine
from src.engines.serper_engine import SerperGoogleEngine
from src.engines.tavily_grounding import TavilyGroundingEngine
from src.exceptions import EngineError

EngineType = Literal["mock", "gemini", "openrouter", "tavily", "serper"]

from src.logger import get_logger

logger = get_logger("engine.factory")

_DEFAULT_MODEL = {
    "gemini": "gemini-2.5-flash",
    "tavily": "tavily-search-v1",
    "serper": "google-serp-th",
    "mock": "mock-synthetic-v1",
}
# last-resort id if the live OpenRouter free list can't be fetched
_OPENROUTER_FALLBACK = "meta-llama/llama-3.3-70b-instruct:free"


def _resolve_openrouter_model(api_key: str | None) -> str:
    """OpenRouter free ids go stale constantly and many are chat-unusable, so
    resolve one that actually answers a probe request."""
    try:
        from src.engines.model_registry import OpenRouterModelRegistry

        return OpenRouterModelRegistry(api_key=api_key).resolve_working_free_model()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenRouter free-model resolution failed (%s); using fallback", exc)
        return _OPENROUTER_FALLBACK


class EngineFactory:
    @staticmethod
    def create(
        engine_type: EngineType = "mock",
        model_name: str | None = None,
        api_key: str | None = None,
    ) -> BaseObservationEngine:
        """``api_key`` is a per-call bring-your-own-key. When None the engine
        falls back to its provider env var. The key is never logged or persisted."""
        model = model_name or _DEFAULT_MODEL.get(engine_type)
        if engine_type == "gemini":
            return GeminiObservationEngine(model_name=model, api_key=api_key)
        if engine_type == "openrouter":
            model = model_name or _resolve_openrouter_model(api_key)
            return OpenRouterEngine(model_name=model, api_key=api_key)
        if engine_type == "tavily":
            return TavilyGroundingEngine(model_name=model, api_key=api_key)
        if engine_type == "serper":
            return SerperGoogleEngine(model_name=model, api_key=api_key)
        if engine_type == "mock":
            return MockObservationEngine(model_name=model)
        raise EngineError(f"Unsupported engine type: {engine_type}")
