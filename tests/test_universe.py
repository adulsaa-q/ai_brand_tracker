import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.universe.generator import QueryUniverseGenerator

def test_query_universe_generation_reproducibility():
    gen = QueryUniverseGenerator()
    set1 = gen.generate_queries(count=5, seed=123)
    set2 = gen.generate_queries(count=5, seed=123)
    
    assert len(set1) == 5
    assert set1[0]["text_th"] == set2[0]["text_th"]
    assert set1[0]["category"] == set2[0]["category"]
    assert set1[0]["is_control_set"] is False

def test_query_universe_control_set():
    gen = QueryUniverseGenerator()
    ctrl = gen.get_control_benchmark_set()
    assert len(ctrl) == 30
    assert ctrl[0]["is_control_set"] is True

def test_query_universe_variety():
    gen = QueryUniverseGenerator()
    queries = gen.generate_queries(count=20, seed=999)
    categories = set(q["category"] for q in queries)
    assert len(categories) >= 3
