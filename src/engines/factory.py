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

_DEFAULT_MODEL = {
    "gemini": "gemini-2.5-flash",
    "openrouter": "deepseek/deepseek-chat:free",
    "tavily": "tavily-search-v1",
    "serper": "google-serp-th",
    "mock": "mock-synthetic-v1",
}


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
            return OpenRouterEngine(model_name=model, api_key=api_key)
        if engine_type == "tavily":
            return TavilyGroundingEngine(model_name=model, api_key=api_key)
        if engine_type == "serper":
            return SerperGoogleEngine(model_name=model, api_key=api_key)
        if engine_type == "mock":
            return MockObservationEngine(model_name=model)
        raise EngineError(f"Unsupported engine type: {engine_type}")
