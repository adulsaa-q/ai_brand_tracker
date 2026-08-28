from __future__ import annotations
from typing import Literal, Optional
from src.engines.base import BaseObservationEngine
from src.engines.mock_engine import MockObservationEngine
from src.engines.gemini_engine import GeminiObservationEngine
from src.engines.openrouter_engine import OpenRouterEngine
from src.exceptions import EngineError

EngineType = Literal["mock", "gemini", "openrouter"]

class EngineFactory:
    @staticmethod
    def create(engine_type: EngineType = "mock", model_name: Optional[str] = None) -> BaseObservationEngine:
        if engine_type == "gemini":
            return GeminiObservationEngine(model_name=model_name or "gemini-2.5-flash")
        elif engine_type == "openrouter":
            return OpenRouterEngine(model_name=model_name or "deepseek/deepseek-chat:free")
        elif engine_type == "mock":
            return MockObservationEngine(model_name=model_name or "gemini-2.5-flash-mock")
        else:
            raise EngineError(f"Unsupported engine type: {engine_type}")
