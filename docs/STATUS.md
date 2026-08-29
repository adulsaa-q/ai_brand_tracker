# Feature status (post remediation phases 0–5)

Honest per-feature state. Updated after implementation, not before.

## North star (not yet met)

Today the platform **observes** how AI answers recommend brands. To answer real
enterprise GEO / GSO / AEO needs it must also **prescribe**: evidence-linked,
owner-assignable actions a marketing team can execute and then measure.

Gap between here and there:

- Recommendations are templated prose, not tied to the specific query, the
  competitor that won it, or the citation/domain that drove it.
- No citation to content-gap mapping (which page/entity to create or improve,
  and where to earn placement).
- No brand-entity consistency check across sources (structured data,
  Wikidata / Wikipedia presence, canonical naming).
- No longitudinal "did our intervention move SoV" loop (needs `/trends`).
- Query universe is 6 intent pillars, not yet a real map of how customers ask.
- Output is a JSON summary, not an exec-ready brief with effort / impact /
  confidence per action.

This is the main product direction, after the UX pass.

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
| Live OpenRouter free-model list | `GET /api/v1/models` fetches fresh every call; dashboard model dropdown when engine = openrouter |
| Bring-your-own provider key | `X-Provider-Key` header / browser localStorage / env; never logged or persisted (only `byok` flag) |
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
- **UX / UI rethink** — the dashboard is now honest and wired to the backend, but
  the information architecture (tab structure, the "executive terminal" hero card,
  how surfaces and the 4-stage memo are presented) needs a proper design pass.
  Deliberately deferred — to be done gradually, not in this pass.
