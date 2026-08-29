# Feature status (post remediation phases 0–4)

Honest per-feature state. Updated after implementation, not before.

## Shipped — works and is tested

| Feature | Notes |
| --- | --- |
| Query Universe Generator | 6 intent pillars × persona, seeded, reproducible |
| Multi-vertical config (6 sectors) + custom verticals via API | |
| Mock engine | deterministic across processes (SHA-256 seed); labelled `synthetic` everywhere |
| DuckDB star schema persistence | `dim_brand/dim_query/fact_observation/fact_brand_mention/fact_citation`, all `run_id`-tagged; single analytical source of truth |
| Pipeline run_stats | requested / successful / provider_errors / persistence_failures / parse_failures, surfaced in API + Streamlit |
| Observation identity | UUID4; regression-tested for uniqueness under load |
| Provenance | `provider` + `answer_surface` + `parse_status` + `prompt_version` per observation |
| Analytics from canonical store | `AnalyticsRepository` reloads from DuckDB; analytics never run on the raw in-memory list |
| SoV / NRS per answer surface | headline = `generative_answer` only; full `by_surface` breakdown kept (ADR 0002) |
| Opportunity Finder | canonical focal-brand resolution (id/name/alias); no fabricated `%` impact |
| Citation influence graph, claim audit | |
| FastAPI REST + SSE-style progress polling | |
| Auth baseline | API-key dependency, open vs enforced mode, read-gating flag |
| Scan abuse limits | concurrency + daily quota → 429; `count` bounded 1..200 |
| Health endpoint | liveness vs dependency checks (config + DuckDB), auth mode |
| Web dashboard ↔ backend | scan → progress → metrics wired; LIVE / SYNTHETIC / NO-DATA / ERROR states |
| Packaging + CI | wheel builds, editable install, import smoke, ruff, tests |

## Experimental — real code, not production-hardened

| Feature | Gap |
| --- | --- |
| Gemini / OpenRouter engines | exercised by unit tests with mocked transport only; no live-key integration test in CI |
| Gemini JSON-repair retry | one bounded retry; not measured against a real eval set |
| Serper / Tavily engines | brand detection is substring match on titles/snippets |
| Streamlit dashboard | reads the global `latest_run_summary.json`; single-vertical view |

## Demo / synthetic only

| Feature | Notes |
| --- | --- |
| `mock` engine output | fabricated; every surface labels it `synthetic` |
| `dashboard/web/index.html` bundled `verticalDatasets` | shown only in explicit demo mode with a red banner |
| What-If Strategy Simulator (`src/analytics/simulator.py`) | hardcoded lever weights; no endpoint, dashboard-only client-side model |
| `information_lag` | reports grounding rate only; the time-lag estimate was removed as fabricated |

## Roadmap — not implemented

- Analytics as native DuckDB SQL aggregates (currently reload-then-compute in Python)
- Live-key integration tests for paid engines; provider cost/token budgeting
- Persistent job store (task state is in-process, lost on restart)
- Per-key rate limiting + audit log of who triggered which scan
- Inlined web assets (dashboard still loads Tailwind / Chart.js / fonts from CDN)
- Real Thai-competency model eval to replace the removed `benchmark_thai_competency`
- Temporal-context slicing UI (data is captured at run grain; no UI to compare runs across events)
