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


class EngineFactory:
    @staticmethod
    def create(engine_type: EngineType = "mock", model_name: str | None = None) -> BaseObservationEngine:
        if engine_type == "gemini":
            return GeminiObservationEngine(model_name=model_name or "gemini-2.5-flash")
        elif engine_type == "openrouter":
            return OpenRouterEngine(model_name=model_name or "deepseek/deepseek-chat:free")
        elif engine_type == "tavily":
            return TavilyGroundingEngine(model_name=model_name or "tavily-search-v1")
        elif engine_type == "serper":
            return SerperGoogleEngine(model_name=model_name or "google-serp-th")
        elif engine_type == "mock":
            return MockObservationEngine(model_name=model_name or "gemini-2.5-flash-mock")
        else:
            raise EngineError(f"Unsupported engine type: {engine_type}")
