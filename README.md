# Thailand AI Market & Decision Intelligence Platform

Tracks how generative AI answers (Gemini, OpenRouter models) and search surfaces
(Google SERP via Serper, web retrieval via Tavily) talk about brands when Thai
consumers ask "ซื้อ/ใช้บริการที่ไหนดี" — measuring **AI Share of Voice**,
recommendation rank, sentiment, and which web domains drive those answers, then
turning it into a 4-stage decision memo (*What → Why → So what → Now what*).

> **Status:** remediation phases 0–4 complete. See `docs/STATUS.md` for the
> honest per-feature breakdown (Shipped / Experimental / Demo / Roadmap) and
> `docs/adr/` for the architecture decisions.

---

## 1. Architecture (as built)

```
CLI / FastAPI  ─┬─►  run_intelligence_pipeline (src/runner.py)
                │
                │   QueryUniverseGenerator ──► EngineFactory ──► one engine:
                │      config/*.yaml            mock | gemini | openrouter | serper | tavily
                │                                     │  (shared retry/backoff, typed errors,
                │                                     │   versioned prompts, UUID obs ids)
                │                                     ▼
                │                          RawObservation  (provider + answer_surface + parse_status)
                │                                     │
                │                                     ▼
                │                          DuckDB star schema  ── the single analytical store
                │                          dim_brand · dim_query · fact_observation
                │                          fact_brand_mention · fact_citation   (all tagged run_id)
                │                                     │
                │        AnalyticsRepository.load_observations(run_id)  ◄── analytics read HERE
                │                                     ▼
                │        MarketMetrics (per answer_surface) · OpportunityFinder ·
                │        CitationInfluence · ClaimIntelligence · InformationLag
                │                                     ▼
                └──►  data/run_<id>.json  +  data/latest_run_summary_<vertical>.json  (atomic)

FastAPI (src/api.py, :8000)  — auth via src/security.py, scan concurrency/quota limits
   GET  /api/v1/health                     liveness + dependency checks + auth mode
   GET  /api/v1/verticals                  list sectors
   GET  /api/v1/models                     live OpenRouter free-model list
   POST /api/v1/verticals        [write]   create/replace a custom sector
   POST /api/v1/scan             [write]   queue a background scan (X-Provider-Key for BYOK)
   GET  /api/v1/scan/{id}/progress         live progress + run_stats
   GET  /api/v1/metrics/{vertical}         last run summary (or PENDING_SCAN)
   GET  /api/v1/export/{vertical}          CSV / JSON
   GET  /                                  web dashboard (dashboard/web/index.html)

dashboard/web/index.html  — calls the API above; shows LIVE / SYNTHETIC / NO-DATA / ERROR states
dashboard/app.py          — Streamlit view of data/latest_run_summary.json
```

---

## 2. Quickstart

```bash
pip install -e ".[dev]"                 # core + tests
pip install -e ".[dev,dashboard]"       # + Streamlit dashboard

# run a scan (mock = deterministic, zero cost, clearly labelled synthetic)
python -m src.cli run --vertical ev_automotive_th --count 30 --engine mock

# real generative run (needs GEMINI_API_KEY)
python -m src.cli run --vertical ecommerce_retail_th --count 15 --engine gemini

# full-stack server + web dashboard
python -m src.cli serve --port 8000      # http://localhost:8000
```

### API security

`AIBT_API_KEYS` unset → **open mode** (writes allowed, logged, `/health` says
`auth_mode: "open"`). Set it (comma-separated) to require `X-API-Key` /
`Authorization: Bearer` on writes. See `SECURITY.md`.

### Bring-your-own OpenRouter key + live free models

```bash
python -m src.cli models                              # live free-model list
python -m src.cli run --engine openrouter --model deepseek/deepseek-chat:free ...
```

The free tier changes constantly, so the list is always fetched live
(`GET /api/v1/models`). Callers can pass a key per request via `X-Provider-Key`
(header) instead of the `OPENROUTER_API_KEY` env var — it is used for that run
and never stored. In the web dashboard: *API settings* → OpenRouter key (kept in
your browser only), then pick a model in the scan dialog.

---

## 3. Verticals

Pre-configured: `ecommerce_retail_th`, `ev_automotive_th`, `banking_fintech_th`,
`real_estate_th`, `hospital_healthcare_th`, `fnb_coffee_th`. Add your own via
`POST /api/v1/verticals` or by editing `config/entities.yaml`.

---

## 4. Tests & quality

```bash
pytest tests/ -q          # unit + contract + integration + acceptance
ruff check . && ruff format --check .
python -m build --wheel   # packaging smoke
```

CI (`.github/workflows/ci.yml`) runs editable install, wheel build, import
smoke, ruff, and the full test suite.

---

## 5. Project layout

```
config/            entities.yaml · control_benchmark_set.yaml · thai_personas.yaml
src/
  runner.py        end-to-end pipeline (persist -> reload from DuckDB -> analyse)
  api.py           FastAPI REST + static mount
  security.py      auth dependency + scan limiter
  prompts.py       versioned prompt registry
  ids.py           UUID observation / run ids
  brands.py        canonical brand-identity resolution
  universe/        QueryUniverseGenerator + Thai temporal calendar
  engines/         mock · gemini · openrouter · serper · tavily  (+ _http, _parsing)
  storage/         duckdb_store.py  (SQLite dropped — ADR 0001)
  analytics/       metrics · opportunity · citation_graph · claim_intelligence ·
                   information_lag · simulator · repository
docs/adr/          0001 single store · 0002 answer surfaces + temporal context
docs/STATUS.md     per-feature Shipped/Experimental/Demo/Roadmap
```

---

## 6. License

MIT. Developed by Adul Sa-a (Q).
