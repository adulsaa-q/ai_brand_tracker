import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engines.model_registry import OpenRouterModelRegistry


def test_model_registry_free_discovery():
    reg = OpenRouterModelRegistry()
    candidates = reg.get_free_tier_candidates()
    assert isinstance(candidates, list)

def test_thai_competency_benchmark():
    reg = OpenRouterModelRegistry()
    bench = reg.benchmark_thai_competency("mock-free-model")
    assert "thai_comprehension_score" in bench
    assert bench["thai_comprehension_score"] > 80
