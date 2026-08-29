# Data Source & API Feasibility Matrix (2026)

**Auditor:** AI Systems Architect & Data Compliance Lead (Q)  
**Date:** August 2026  
**Operating Principle:** Free-First, Legally Compliant, High-Reliability Architecture

---

## 1. Source Classification Matrix

| Source / Provider | Data Type | Access Method | Cost Tier | Rate Limits | Thailand Coverage | Commercial / Legal Risk | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Search Grounding (Gemini)** | Real-time Web SERP + AI Citations | Official Google GenAI SDK | **Tier 1 (Free Quota)** | 15 RPM (Flash) | Excellent (Native Thai) | Compliant via Official API | **CORE OBSERVATION ENGINE** |
| **OpenRouter Free Tier Models** | Multi-Model AI Responses & Extraction | OpenRouter REST API | **Tier 0 (Free / $0)** | Dynamic (20-50 RPM) | Good-Excellent (Qwen, DeepSeek, Llama) | Compliant via OpenRouter Terms | **CORE ANALYSIS ENGINE** |
| **Google Trends** | Relative search interest & trend spikes | PyTrends / Google Trends RSS | **Tier 0 (Free)** | Moderate (Backoff required) | High (Thailand region `TH`) | Low risk for aggregate signals | **SECONDARY SIGNAL (Phase F)** |
| **ETDA / data.go.th** | Public Thai digital commerce stats | Open Data Portal API / CSV | **Tier 0 (Free)** | Unlimited | Official National Data | Public Domain / Open Gov License | **CALIBRATION BENCHMARK** |
| **Shopee / Lazada Public Feeds** | Pricing, Rating, Review counts | Official Open Platform API | **Tier 3 (Key required)** | Partner specific | Full Thailand catalog | ToS strictly requires Official API; no aggressive scraping | **OPTIONAL COMMERCE (Phase I)** |
| **Pantip / Web Communities** | Consumer Sentiment & Discussions | RSS / Semantic search grounding | **Tier 1 (Via AI Grounding)** | N/A (Grounding index) | Thai specific | Low risk via LLM grounding citation | **INDIRECT VIA CITATIONS** |
| **Perplexity Sonar / Pro Search** | AI Search with full citations | Perplexity API | **Tier 4 (Paid)** | By Plan | Excellent | Compliant via Paid API | **OPTIONAL ENTERPRISE UPGRADE** |

---

## 2. Decision Rules on External Data Ingestion
1. **Never scrape behind login walls or anti-bot protections.**
2. **Prefer LLM Grounding Metadata:** Let Gemini / Search Providers query live web indexes natively rather than maintaining fragile scrapers.
3. **Graceful Degradation:** If any paid or rate-limited API becomes unavailable, the system automatically falls back to Mock / Free OpenRouter / Cached Snapshot without crashing.
