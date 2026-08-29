# tests/test_engines.py
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engines import (
    EngineFactory,
    GeminiObservationEngine,
    MockObservationEngine,
    OpenRouterEngine,
    SerperGoogleEngine,
    TavilyGroundingEngine,
)
from src.exceptions import EngineError


def test_engine_factory_creation():
    mock_eng = EngineFactory.create("mock")
    assert isinstance(mock_eng, MockObservationEngine)

    gemini_eng = EngineFactory.create("gemini")
    assert isinstance(gemini_eng, GeminiObservationEngine)

    or_eng = EngineFactory.create("openrouter")
    assert isinstance(or_eng, OpenRouterEngine)

    tav_eng = EngineFactory.create("tavily")
    assert isinstance(tav_eng, TavilyGroundingEngine)

    serp_eng = EngineFactory.create("serper")
    assert isinstance(serp_eng, SerperGoogleEngine)


def test_engine_factory_invalid():
    with pytest.raises(EngineError):
        EngineFactory.create("invalid_engine_type")


def test_mock_engine_observe():
    mock_eng = MockObservationEngine()
    obs = mock_eng.observe(query_id="q_test_1", query_text="ซื้อสกินแคร์ที่ไหนดี", target_brands=["Shopee", "Konvy"])
    assert obs.query_id == "q_test_1"
    assert len(obs.brand_mentions) == 2
    assert len(obs.citations) >= 1
