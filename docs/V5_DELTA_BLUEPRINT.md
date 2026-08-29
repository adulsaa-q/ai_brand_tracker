# 🏛️ AI BRAND TRACKER V5 — DELTA BLUEPRINT & FORENSIC AUDIT
## Transforming V4 into a Production-Grade Thailand AI Market & Decision Intelligence Platform

> **Author:** Autonomous Repository Engineering Team  
> **Date:** August 2026  
> **Target Status:** V5.0.0 Enterprise Production Platform  
> **Architecture Foundation:** Universal Multi-Vertical Engine · Zero-Terminal Self-Service · FastAPI Microservices · DuckDB Lakehouse · Architectural Monochromatic Luxury (Style Q)

---

# 1. FORENSIC AUDIT: V4 BLUEPRINT vs. ACTUAL REPOSITORY vs. V5 NORTH STAR

| Area | V4 Blueprint Stated | Repo Actually Has | Gap | Business Impact | Technical Risk | V5 Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Frontend UI/UX** | Self-Service Web UI with Industry Dropdown, Add Brand Wizard, 1-Click Scan Modal | Static single-vertical SPA with hardcoded beauty dataset in JS | **High:** No dynamic REST API bindings, no interactive scan launcher modal, no live SSE progress bar | Users cannot add brands or run scans from UI | Low (pure frontend enhancement) | **REPLACE & UPGRADE:** Implement full dynamic client with REST API sync, live progress streaming, and drilldown |
| **Backend API** | FastAPI Micro-Engine (`src/api.py`) with REST & SSE streaming | No `src/api.py` exists yet; only CLI `python src/cli.py` & basic `http.server` | **Critical:** Non-technical users cannot operate the system without developer | Zero-terminal promise unfulfilled | Low (FastAPI is pre-installed) | **BUILD NEW:** Implement `src/api.py` with full REST + Background Scan Worker + SSE Progress stream |
| **Universal Entities** | Generic multi-vertical configuration for any industry | Only `ecommerce_retail_th` with 9 beauty brands | **High:** Cannot analyze EV, Banking, Real Estate, Hospitals out of the box | Restricted to one niche | Low | **EXPAND & REFACTOR:** Implement 6 benchmark verticals in `config/entities.yaml` + Dynamic In-Memory/DB creation |
| **Query Universe** | Domain-adaptive generation across 6 intent pillars | Hardcoded beauty cosmetic templates in `generator.py` | **High:** Exploratory generator only works for cosmetics | Nonsensical queries if used for EV or Banking | Low | **REFACTOR V2:** Make `QueryUniverseGenerator` domain-adaptive with generic intent slots & category configs |
| **Observation vs Analysis** | Clear architectural separation | Separate modules exist (`src/engines/` and `src/analytics/`) | **Low:** Good foundation, needs explicit provenance tracking | Transparent trust | Low | **KEEP & ENHANCE:** Add explicit `evidence_class` (OBSERVED, DERIVED, INFERRED, SIMULATED) |
| **Model Registry** | OpenRouter dynamic qualification & Thai benchmark | `ModelRegistry` in `src/engines/model_registry.py` with static free models | **Medium:** Needs automated health check and benchmark scoring | Free models may drift | Low | **IMPROVE:** Enhance dynamic qualification & fallback tiers |
| **Storage & Lakehouse** | DuckDB Star Schema + SQLite dual store | Fully working in `src/storage/duckdb_store.py` & `sqlite_store.py` | **None:** Rock-solid star schema | Provenance preserved | None | **KEEP & EVOLVE:** Preserve all tables, add vertical filtering to queries |
| **Opportunity Engine** | What → Why → So What → Now What decision framework | Basic `OpportunityFinder` with `CATEGORY_VISIBILITY_GAP` | **Medium:** Needs structured action memo and prioritization | Executive value | Low | **UPGRADE:** Transform into comprehensive 4-stage Decision Intelligence engine |
| **CLI & Automation** | Unified `serve` command for web + api | Separate `web` command (only runs static python http.server) | **Medium:** Users must run multiple commands | Operational friction | Low | **UNIFY:** `python src/cli.py serve` launches FastAPI + serves UI on a single unified port |

---

# 2. WHAT V4 GOT RIGHT vs. WHAT V4 GOT WRONG

### 🟢 What V4 Got Right
1. **The Zero-Terminal Principle:** Recognizing that 95% of business executives cannot and should not use terminal commands.
2. **The 6 Intent Pillars:** Structuring Thai consumer queries into *Promotion, Trust/Authenticity, Variety, Delivery/Speed, Payment/0%, and Customer Service*.
3. **Star Schema Lakehouse:** Separating `dim_brand`, `dim_query`, `fact_observation`, `fact_brand_mention`, and `fact_citation` in DuckDB.
4. **Architectural Monochromatic Materiality (Style Q):** `#F2F0EF`, `#C9C8C7`, `#949392`, `#66615E`, and Black with 1px hairlines and editorial typography.

### 🔴 What V4 Got Wrong / Incomplete
1. **Hardcoded Query Templates:** `QueryUniverseGenerator` hardcoded cosmetic terms (`สกินแคร์เคาน์เตอร์แบรนด์`, `เซรั่ม`) instead of using domain-adaptive templates.
2. **Missing API Server:** Blueprint documented `src/api.py` but it was not yet created in code.
3. **Static UI Dataset:** `dashboard/web/index.html` contained hardcoded beauty data arrays in JS instead of pulling dynamically from REST endpoints.
4. **Lack of Live Scan Runner Modal:** The web UI had no modal to trigger live scans, select engines, or watch live SSE progress.

---

# 3. V5 ARCHITECTURAL BLUEPRINT

```mermaid
graph TD
    subgraph UI [Executive Self-Service Web Terminal - Style Q]
        TopBar[Top Bar: Industry Selector Dropdown · + New Industry · ⚡ Run Live AI Scan · Export]
        Hero[Asymmetric Hero: Dominant Market Signal & Supporting Key Indicators]
        Tabs[Navigation Rail: 01 Market Share · 02 Citations · 03 Strategy · 04 Simulator · 05 Evidence]
        Modal_New[Modal: + Add New Industry & Brand Universe Wizard]
        Modal_Scan[Modal: 1-Click AI Scan Launcher with Live Progress 0-100%]
    end

    subgraph API [FastAPI Backend Service: src/api.py]
        E_Verts[GET /api/v1/verticals · POST /api/v1/verticals]
        E_Scan[POST /api/v1/scan - Async Background Tasks]
        E_Prog[GET /api/v1/scan/{id}/progress - SSE / Polling]
        E_Metrics[GET /api/v1/metrics/{vertical_id} - DuckDB Analytics]
        E_Queries[GET /api/v1/queries/{vertical_id} - Evidence Archive]
        E_Export[GET /api/v1/export/{vertical_id} - CSV / JSON]
        E_Static[GET / - Static Web App]
    end

    subgraph CoreEngine [Universal Intelligence Engine]
        GenV2[Domain-Adaptive Query Universe Generator V2]
        Factory[Multi-Engine Observation Layer: Gemini · Tavily · OpenRouter · Mock]
        Registry[Dynamic ModelRegistry: Tier S/A/B Qualification]
        Decision[Decision Intelligence: Opportunities · Actions · Claims · Freshness]
    end

    subgraph DataLakehouse [DuckDB Star Schema + SQLite]
        DuckDB[(DuckDB: dim_brand, dim_query, fact_obs, fact_mention, fact_cite)]
        SQLite[(SQLite: Transactions & Raw Runs)]
    end

    %% Wiring
    Modal_New -->|Create Industry| E_Verts
    Modal_Scan -->|Trigger Scan| E_Scan
    E_Scan --> GenV2 --> Factory --> Decision --> DuckDB & SQLite
    E_Scan -.->|Stream Progress| E_Prog -.-> Modal_Scan
    E_Metrics -->|JSON Analytics| Hero & Tabs
    TopBar -->|Switch Vertical| E_Metrics
```

---

# 4. IMPLEMENTATION ROADMAP (WAVES 1 TO 5)

### Wave 1: Domain-Adaptive Query Universe V2 & Universal Entities
* Update `config/entities.yaml` with 6 core Thai verticals:
  1. `ecommerce_retail_th` (Beauty & E-Commerce)
  2. `ev_automotive_th` (Electric Vehicles & Auto)
  3. `banking_fintech_th` (Banking & Digital FinTech)
  4. `real_estate_th` (Property & Condominiums)
  5. `hospital_healthcare_th` (Private Hospitals & Healthcare)
  6. `fnb_coffee_th` (F&B & Coffee Retail Chains)
* Refactor `src/universe/generator.py` into a fully domain-adaptive generator that accepts ANY vertical configuration and synthesizes relevant Thai consumer queries across the 6 intent pillars.

### Wave 2: FastAPI Backend Engine (`src/api.py`)
* Create `src/api.py` with complete REST endpoints:
  * `/api/v1/verticals` (List & Create custom verticals)
  * `/api/v1/scan` (Async background scan worker supporting Gemini, Tavily, OpenRouter, Mock)
  * `/api/v1/scan/{task_id}/progress` (Live scan status, percentage, current query, completed count)
  * `/api/v1/metrics/{vertical_id}` (Aggregated SoV, Mean Rank, NRS, Positive %, Leaderboard)
  * `/api/v1/citations/{vertical_id}` (Authority sources & domain influence)
  * `/api/v1/opportunities/{vertical_id}` (High-impact decision intelligence actions)
  * `/api/v1/queries/{vertical_id}` (Verifiable forensic prompt & response archive)
  * `/api/v1/export/{vertical_id}` (CSV/JSON download)
  * Static file mount serving `dashboard/web/index.html` seamlessly on the same port!

### Wave 3: Decision Intelligence & Opportunity Engine
* Enhance `src/analytics/opportunity.py` to produce **What is happening → Why → So what → Now what** structured action memos with effort/impact scoring (P1 Critical, P2 Defensive, P3 Recovery).
* Enhance `src/analytics/simulator.py` to calculate dynamic What-If projections based on active brand levers.

### Wave 4: Self-Service Executive UI/UX Overhaul (`dashboard/web/index.html`)
* Integrate full REST client with automatic fallback to high-fidelity seed data if offline.
* Add **Top Bar Controls**:
  * Industry Selector dropdown (switches dataset instantly).
  * `[+ New Industry]` button opening the **Add Brand Universe Wizard**.
  * `[⚡ Run Live AI Scan]` button opening the **1-Click AI Scan Launcher**.
  * `[Export Data]` button downloading CSV/JSON.
* Add **Interactive Modals**:
  * **Modal 1: Add Industry & Brands Wizard** (Vertical name, focal brand, competitor list with auto-tagging).
  * **Modal 2: 1-Click AI Scan Launcher** (Select Gemini/Tavily/OpenRouter/Mock, choose sample size, click "Start AI Scan").
  * **Modal 3: Live Progress Tracker** (0% to 100% animated progress bar with live query counter and status logs).
* Preserve exact Architectural Monochromatic Luxury palette (`#F2F0EF`, `#C9C8C7`, `#949392`, `#66615E`, Black) with 1px hairlines.

### Wave 5: Unified CLI & Automated Test Suite
* Update `src/cli.py` to support `python src/cli.py serve --port 8000` (launches FastAPI and opens browser).
* Create comprehensive test suite `tests/test_api.py` and `tests/test_universe_v2.py`.
* Validate 100% test pass rate with `pytest tests/` and 0 lint errors with `ruff check .`.

---

# 5. ACCEPTANCE CRITERIA (EXECUTIVE QUESTIONS VERIFIED)

1. ✅ **Are we winning or losing?** Answered instantly on Executive Hero (SoV % vs Nearest Competitor).
2. ✅ **Who is beating us and where?** Answered on Market Share Matrix & Category Gaps.
3. ✅ **Which sources influence AI recommendations?** Answered on Citation Authority Network.
4. ✅ **What should we do first?** Answered on Prioritized Action Memo (P1 High Impact / Low Effort).
5. ✅ **Can a non-technical user run scans and add industries?** Answered with 100% Zero-Terminal Web UI.
