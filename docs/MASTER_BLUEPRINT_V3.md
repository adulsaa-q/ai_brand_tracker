# MASTER BLUEPRINT V3 — Thailand AI Market & Decision Intelligence Platform

**Document Version:** 3.0.0-PROD  
**Author:** Principal AI Systems & Product Architect (Q)  
**Target Repository:** `https://github.com/adulsaa-q/ai_brand_tracker`  
**Date:** August 2026  
**Status:** APPROVED FOR PRODUCTION IMPLEMENTATION  

---

## 1. Executive Summary
The transition from `ai_brand_tracker` (v1/v2) to the **Thailand AI Market & Decision Intelligence Platform (v3)** shifts the paradigm from simple string-matching Generative Engine Optimization (GEO) into an enterprise-grade, multi-vertical **Decision Intelligence Platform**. 

The platform continuously answers 5 foundational strategic questions for business executives:
1. **WHAT HAPPENED?** Which brands, products, and channels are winning AI recommendations across Thai consumer touchpoints?
2. **WHY DID IT HAPPEN?** What authoritative web sources, social sentiments, price claims, and algorithmic biases drove those recommendations?
3. **WHERE ARE WE LOSING?** In which customer personas, intent categories, and Thai language styles is our brand invisible or misrepresented?
4. **SO WHAT?** What is the business impact on market share, consumer trust, and channel revenue?
5. **NOW WHAT?** What specific, prioritized, high-impact interventions (content, PR, marketplace optimization, structured metadata) should the brand execute immediately?

---

## 2. Existing Repository Assessment & Gap Analysis

| Component | Legacy State (v1/v2) | Flaw & Business Risk | Target State (v3) |
| :--- | :--- | :--- | :--- |
| **Mention Detection** | Substring search (`in`) | False Positives/Negatives | Pydantic Schema-enforced Extraction |
| **Ranking Logic** | Character offset (`.find()`) | Disclaimers ranked #1 | Multi-attribute Recommendation Strength |
| **LLM Provider** | Single Gemini 2.5 Flash | Quota exhaustion, lock-in | Multi-Provider (OpenRouter Free + Gemini + Mock) |
| **Query Engine** | 30 static hardcoded prompts | Zero variance & exploration | Query Universe Engine (Controlled Randomness) |
| **Persistence** | Flat SQLite append-only | Data duplication, slow aggregations | DuckDB Lakehouse Star Schema + SQLite |
| **Visualization** | Static Jupyter Notebook PNGs | Unusable by executives | Interactive 6-Tab Decision Portal |

---

## 3. Product Vision & Multi-Vertical Value Proposition

### 3.1 Core Question
> *"What are Thai consumers asking, discovering, and comparing across AI and search ecosystems; why do specific brands win; what sources shape those answers; and what should the business do next?"*

### 3.2 Generic Multi-Vertical Architecture
The platform is decoupled from beauty e-commerce. It natively models any vertical through generic entities (`Entity`, `Brand`, `Product`, `QueryCluster`, `Observation`, `Citation`, `Claim`).

**Supported Verticals:**
- **Vertical 1 (Active):** E-Commerce & Beauty Retail (`Shopee`, `Lazada`, `Konvy`, `EVEANDBOY`, `Beautrium`, `Sephora`, `Watsons`, `Boots`)
- **Vertical 2 (Roadmap):** Banking & FinTech (`KBank`, `SCB`, `Bangkok Bank`, `Krungthai`, `TTB`)
- **Vertical 3 (Roadmap):** Healthcare & Private Hospitals (`Bumrungrad`, `BDMS`, `Samitivej`, `Praram 9`)
- **Vertical 4 (Roadmap):** Automotive & EV (`BYD`, `Tesla`, `MG`, `Toyota`, `Honda`)

---

## 4. Thai Digital Consumer Modeling (Query Universe Engine)

$$\mathcal{Q} = 	ext{Sampling}(	ext{Persona} 	imes 	ext{Intent} 	imes 	ext{Channel} 	imes 	ext{Language Style} 	imes 	ext{Temporal Context} 	imes 	ext{Concern})$$

### 4.1 Persona Dimensions
- **Gen-Z Trend Hunter (18-24):** Visual discovery, TikTok Shop / Lemon8 slang, budget conscious (<500 THB), acne/oil control focus.
- **Office Professional (25-39):** Counter brands, Sephora / Central online, authenticity guarantee, weekend delivery, anti-aging.
- **Value-Driven Family / Provincial Buyer (30-55):** Shopee/Lazada free shipping vouchers, COD, bulk purchase, formal Thai.
- **Skincare Enthusiast / Ingredient Nerd:** Dermatologist formulas, Konvy/Watsons, active ingredients (Niacinamide, Retinol).

### 4.2 Controlled Randomness & Dual-Set Protocol
1. **Invariant Control Benchmark Set (30 Fixed Queries):** Run identically every cycle to guarantee longitudinal validity without confounding variance.
2. **Dynamic Exploratory Set ($N$ Sampled Queries):** Seeded pseudo-random sampling for rapid discovery of emerging trends.

---

## 5. Provider Orchestration & Zero-Cost Model Tiering

```
Tier 0 (Free / Zero Key): MockObservationEngine (Offline testing, CI/CD, local dev)
Tier 1 (Free Cloud Quota): Gemini 2.5 Flash with Google Search Grounding
Tier 2 (Free OpenRouter Tier): DeepSeek-R1-Free, Llama-3.3-70B-Free, Qwen-2.5-72B-Free
Tier 3 (Optional Paid / Enterprise): Perplexity Sonar, GPT-4o Search, Claude 3.7 Sonnet
```

---

## 6. Mathematical Metric Definitions

### 6.1 AI Share of Voice (SoV)
$$	ext{SoV}_b = rac{\sum_{i=1}^{N} \mathbb{I}(	ext{brand } b 	ext{ mentioned in query } i)}{N} 	imes 100\%$$

### 6.2 Net Recommendation Score (NRS)
$$	ext{NRS}_b = rac{1}{|M_b|} \sum_{m \in M_b} \left( w_{	ext{intent}}(m) 	imes rac{1}{\sqrt{	ext{rank}(m)}} 	imes 	ext{sentiment\_weight}(m) ight)$$

---

## 7. Storage & Lakehouse Schema Design
- **SQLite (`data/intelligence.db`):** Transactional state & metadata.
- **DuckDB (`data/intelligence.duckdb`):** Analytical Star Schema (`dim_brand`, `dim_query`, `fact_observation`, `fact_brand_mention`, `fact_citation`).

---

## 8. Definition of Done & Quality Gates
- [x] Zero data loss migration from v1 baseline.
- [x] 100% test pass rate on Pytest suite.
- [x] Dual-set Query Universe execution.
- [x] Interactive 6-Tab Streamlit Executive Dashboard with Plotly visuals.
- [x] Complete documentation suite.
