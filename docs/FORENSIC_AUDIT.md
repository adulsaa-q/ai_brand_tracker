# Forensic Audit & Architecture Legacy Review
**Project:** `ai_brand_tracker` → `thailand-ai-market-intelligence`
**Auditor:** Principal AI Systems & Data Architect (Q)
**Date:** 2026-08-28

---

## 1. Executive Summary
The legacy `ai_brand_tracker` project pioneered Generative Engine Optimization (GEO) in Thailand by tracking how Gemini 2.5 recommended major e-commerce and beauty retail platforms across 30 curated prompts.

While the concept was visionary, the v1 implementation had critical structural bottlenecks:
1. **Single LLM Dependency**: Bound strictly to `gemini-2.5-flash`.
2. **Double API Call Waste**: Ran generation first, then string search, then a 2nd API call for sentiment parsing.
3. **Naïve Position Ranking**: Used character offset indexing (`response_text.find(brand)`), which misclassified brands in negative disclaimers as Rank #1.
4. **Static Presentation**: Analysis trapped in a Jupyter Notebook generating static PNGs.
5. **No Domain/Vertical Extensibility**: Hardcoded beauty brands instead of a generic multi-vertical entity model.

---

## 2. Legacy Component Disposition

| Component | Legacy State | Disposition | Target Architecture v3 |
| :--- | :--- | :--- | :--- |
| `collector.py` | Monolithic script, Gemini-only | **REPLACE** | Modular `src/engines/` with Pydantic structured output |
| `config.py` | Reads flat YAML | **REFACTOR** | Pydantic `AppConfig` + `src/models/entities.py` |
| `settings.yaml` | 30 fixed prompts, 8 brands | **EXTEND** | Multi-vertical `config/entities.yaml` + Query Universe Engine |
| `analysis.ipynb` | Matplotlib PNG exporter | **PRESERVE (HISTORICAL)** | Interactive Streamlit Multi-Page Portal (`dashboard/app.py`) |
| `results.db` | Flat SQLite table (`results`) | **MIGRATE** | DuckDB Star Schema (`dim_brand`, `dim_query`, `fact_observation`) |
| `requirements.txt` | Dumped 24 global packages | **REPLACE** | Clean `pyproject.toml` (PEP 621 compliant) |

---

## 3. Core Architectural Upgrades in v3
- **Query Universe Engine**: Controlled randomness sampling across Persona × Intent × Channel × Concern.
- **Single-Pass Structured Extraction**: Pydantic schemas enforce typed JSON responses directly from LLMs.
- **Separation of Observation vs. Analysis**: Measures actual consumer search ecosystems (Gemini Search, Perplexity, GPT Search) while using cheap/free models for synthesis.
- **Local DuckDB Lakehouse**: Sub-millisecond aggregation on millions of signals with 0 recurring cloud costs.
