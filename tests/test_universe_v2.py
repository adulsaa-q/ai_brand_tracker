from src.universe.generator import QueryUniverseGenerator


def test_generator_multi_vertical_ev():
    gen = QueryUniverseGenerator()
    queries = gen.generate_queries(vertical_id="ev_automotive_th", count=10, seed=42)
    assert len(queries) == 10
    for q in queries:
        assert q["vertical_id"] == "ev_automotive_th"
        assert len(q["text_th"]) > 10
        assert q["intent"] in gen.domain_intent_templates


def test_generator_multi_vertical_banking():
    gen = QueryUniverseGenerator()
    queries = gen.generate_queries(vertical_id="banking_fintech_th", count=10, seed=42)
    assert len(queries) == 10
    for q in queries:
        assert q["vertical_id"] == "banking_fintech_th"
        assert len(q["text_th"]) > 10


def test_generator_multi_vertical_real_estate():
    gen = QueryUniverseGenerator()
    queries = gen.generate_queries(vertical_id="real_estate_th", count=10, seed=42)
    assert len(queries) == 10
    for q in queries:
        assert q["vertical_id"] == "real_estate_th"


def test_generator_reproducibility():
    gen = QueryUniverseGenerator()
    q1 = gen.generate_exploratory_queries(vertical_id="hospital_healthcare_th", count=5, seed=123)
    q2 = gen.generate_exploratory_queries(vertical_id="hospital_healthcare_th", count=5, seed=123)
    assert [q["text_th"] for q in q1] == [q["text_th"] for q in q2]
