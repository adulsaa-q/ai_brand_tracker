from src.engines.model_registry import OpenRouterModelRegistry


def test_model_registry_free_discovery():
    reg = OpenRouterModelRegistry()
    candidates = reg.get_free_tier_candidates()
    assert isinstance(candidates, list)  # empty offline, populated with network


def test_registry_has_no_fake_benchmark():
    # Phase 0: benchmark_thai_competency returned hardcoded scores and was removed.
    assert not hasattr(OpenRouterModelRegistry, "benchmark_thai_competency")
