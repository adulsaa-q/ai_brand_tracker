# MASTER_PROMPT coverage

Maps [`MASTER_PROMPT.md`](MASTER_PROMPT.md) (54-section product doctrine) against
the current repo, as of the phase 0–5 remediation. This is a living checklist —
update it as sections land.

Legend: **DONE** · **PARTIAL** · **TODO** (not started) · **N/A** (correctly deferred)

`MASTER_PROMPT.md` is identical to the working copy in `~/PSN-Q/_knowledge/` — the
repo copy is canonical; keep the `_knowledge` one as a pointer or delete it.

---

## Foundation — mostly done

| § | Item | Status | Where |
| --- | --- | --- | --- |
| 1.2 | Audit before rewrite | DONE | `FORENSIC_AUDIT.md`, ADRs, incremental phases |
| 2 | Safe discovery + upgrade branch, nothing destructive | DONE | branch `phase/0-4-remediation` merged |
| 3 | Forensic audit KEEP/REFACTOR/REPLACE/ARCHIVE | DONE | `FORENSIC_AUDIT.md`, `docs/adr/` |
| 4 | Env & secret discovery; never print/commit/log secrets | DONE | `.env` auto-load, masked reporting, BYOK never persisted, `.gitignore` |
| 9 | Separate observation engines from analysis models | DONE | `src/engines/` vs `src/analytics/`; `provider` + `answer_surface` on every obs |
| 10–11 | Query Universe (not fixed prompts) + control + exploration set | DONE | `src/universe/generator.py`, `config/control_benchmark_set.yaml` |
| 36 | Raw data + provenance chain | PARTIAL→ok | obs → `run_id` → DuckDB, raw response stored; dashboard drilldown thin |
| 41 | Serious automated tests | MOSTLY DONE | 75 tests: unit, integration (reconciliation), contract, acceptance, retry/failure, repro. Missing: schema tests, data-quality tests, browser smoke |
| 44 | Project structure | DONE | clean `src/` modules |
| 45 | Dependency modernization (core/dashboard/dev/optional) | DONE | `pyproject.toml` extras |
| 49 | Stop gate: audit → blueprint → review before build | DONE (retro) | this doc |
| 53 | Autonomy + ADRs for important decisions | DONE | `docs/adr/0001`, `0002` |

## Free-first + model intelligence

| § | Item | Status | Notes |
| --- | --- | --- | --- |
| 1.3 | Free-first; capability tiers 0–5 | PARTIAL | every engine runs on a free tier; `data_source_matrix.md` has cost tiers, but no formal Tier 0–5 capability classification |
| 8 | OpenRouter free-model discovery + registry | PARTIAL | live discovery + probe + chat-family filter + auto-select **done**; **no** Thai benchmark (the old fake one was removed), **no** S/A/B/REJECT tiers, **no** scheduled `model_discovery.yml` |
| 37 | Provider architecture (registry, adapters, graceful degradation) | PARTIAL | `EngineFactory` + `BaseObservationEngine`; graceful (errors counted, run continues). No `ProviderRegistry` for search/social/commerce/trend |

## Data + provenance + storage

| § | Item | Status | Notes |
| --- | --- | --- | --- |
| 14 | Entity-first data model (company/brand/product/SKU/creator/source graph) | TODO | still brand + query + observation; no entity graph |
| 21 | Direct vs indirect signal tagging; UI communicates uncertainty | PARTIAL | `answer_surface` + `parse_status`; opportunity confidence labels. No formal `evidence_class` (OBSERVED/DERIVED/INFERRED/SIMULATED), no uncertainty bands in UI |
| 22 | Time-series / change intelligence (full per-obs provenance) | PARTIAL | `run_id`, timestamp, provider, model, `prompt_version`, latency, tokens, `retry_count` all persisted. **No `/trends` endpoint**, no "why did X lose visibility this month" |
| 35 | Storage architecture; ~30 conceptual tables; migrations | PARTIAL | DuckDB chosen (ADR 0001); 5 tables + `run_id`. Missing ~25 tables (social/search/commerce/trend/scores/opportunities/actions/experiments/cost_events/errors); no migration framework (only `CREATE IF NOT EXISTS`) |
| 40 | Data-quality checks (dupes / bad ranks / malformed / anomalies) | PARTIAL | `parse_status`, `persistence_failures`, run raises on 0 obs. No dedicated data-quality module or `data_quality.yml` |
| 43 | Privacy / security / compliance | PARTIAL | `SECURITY.md`, secret handling, untrusted-content model. No data-retention policy, no per-source ToS review |

## Intelligence layer — the main gap

| § | Item | Status | Notes |
| --- | --- | --- | --- |
| 12 | Real signal → query generation (trends/social/marketplace/news) | TODO | queries are template-only |
| 13 | Thai language intelligence — measure if recommendations change by style | PARTIAL | personas carry `language_style`, aliases matched; **not measuring** outcome change across formal/casual/slang |
| 15 | Claim intelligence + verification (SUPPORTED/CONFLICTED/UNVERIFIED/OUTDATED) | PARTIAL | keyword-rule matching only; no verification, no evidence linkage |
| 16 | Source Influence Map (influence × relevance × authority × controllability) | PARTIAL | domain counts + categories; no influence/authority/controllability score, no first-seen/last-seen |
| 17 | Search + SEO + AEO + GEO gap comparison | TODO | only generative + SERP surfaces; no SEO visibility, no cross-surface gap view |
| 18 | Social intelligence | TODO | — |
| 19 | Commerce intelligence (price/rating/reviews/velocity) | TODO | — |
| 20 | Temporal & Thailand event intelligence | PARTIAL | `ThailandTemporalEngine`, `active_events` at run grain; not influencing query sampling |
| 23 | AI information lag | PARTIAL | reports grounding rate only (fake estimate removed); no real lag measurement |
| 24 | Experiment engine (hypothesis → baseline → intervention → before/after) | TODO | — |
| 25 | Business metrics with documented formula / rationale / limitations | PARTIAL | SoV/NRS/sentiment per surface computed; **not** documented in a `metric_definitions.md` |
| 26 | Opportunity Engine (ranked, 0–100 score, why/what competitors have/what to do) | PARTIAL | category-gap detection + 4-stage memo; no 0–100 score, no trend/competition/intent inputs |
| 27 | Recommendation / action engine (priority · effort · expected impact · confidence) | PARTIAL | 4-stage memo has what/why/so-what/now-what + confidence + effort; evidence link weak, no impact×effort ranking |
| 28 | Outcome layer (GSC / GA4 / CRM) | N/A | correctly deferred |
| 33 | AI Executive Analyst (conversational, grounded) | TODO | — |
| 34 | Simulation engine | PARTIAL | `MarketStrategySimulator` exists (hardcoded lever weights, client-side, labelled); not calibrated, no endpoint |

## Dashboard / UX

| § | Item | Status | Notes |
| --- | --- | --- | --- |
| 29 | Premium dashboard, not a Streamlit prototype | PARTIAL | `dashboard/web` is styled and API-wired; Streamlit still present. **Q has flagged the UX for a proper rethink** |
| 30 | Dashboard IA (~15 modules) | PARTIAL | 5 tabs (SoV, citations, 4-stage memo, simulator, query archive). Missing: consumer intel, social, commerce, trend radar, experiment center, system health |
| 31 | Executive home (position / what changed / biggest opportunity / top actions) | PARTIAL | hero shows focal SoV/rank/sentiment + 1 opportunity. No "what changed" (needs longitudinal), no ranked top-3 actions |
| 32 | Chart titles answer questions | PARTIAL | some are question-form, some aren't |

## Automation / observability

| § | Item | Status | Notes |
| --- | --- | --- | --- |
| 38 | Cost-aware orchestration (daily / weekly / monthly / event-driven) | TODO | one weekly workflow only |
| 39 | GitHub Actions suite (ci + daily + weekly + monthly + model_discovery + benchmark + data_quality + dependency_audit + release) | PARTIAL | `ci.yml` (green) + `weekly_tracker.yml` (artifact). Other 7 not built |
| 42 | Observability (status / provider / latency / failure rate / retry / tokens / cost / freshness + health view) | PARTIAL | `run_stats` + `/health` deps + per-obs latency/tokens/retry. No cost estimation, no health dashboard module |
| 46 | Performance (async / batching / caching / dedup) | PARTIAL | retry/backoff + model-resolve cache. **No async** (serial engine calls), no batching |

## Research + product docs

| § | Item | Status | Notes |
| --- | --- | --- | --- |
| 5 | GEO/AEO market research | PARTIAL | `docs/research/geo_market_landscape.md` exists but thin (~30 lines) |
| 6 | Thailand consumer research | PARTIAL | `docs/research/thailand_digital_consumer_2026.md` (~60 lines), citations weak |
| 7 | Data source feasibility matrix | PARTIAL | `docs/research/data_source_matrix.md` (~26 lines); missing most per-source fields the prompt lists |
| 47 | Documentation set (~13 files) | PARTIAL | README, ARCHITECTURE, STATUS, SECURITY, 2 ADRs, 3 research docs. Missing dedicated: `product_vision`, `data_model`, `provider_architecture`, `query_universe`, `metric_definitions`, `automation` |
| 48 | `MASTER_BLUEPRINT_V3.md` (25 sections) | PARTIAL | file exists (~100 lines), not the 25-section depth |

---

## MVP success criteria (§51) — can we answer the 10 questions?

| # | Question | Can answer? |
| --- | --- | --- |
| 1 | Which brands are most visible to AI? | **Yes** |
| 2 | Recommended vs merely mentioned? | **Partly** (recommendation_intent field) |
| 3 | Which competitors gaining / losing? | **No** — needs longitudinal `/trends` |
| 4 | Which Thai consumer intents are we weak in? | **Partly** (category-level, per run) |
| 5 | Does language style affect recommendations? | **No** — not measured |
| 6 | What sources influence AI answers? | **Yes** (citation graph) |
| 7 | What claims are made about us? | **Partly** (keyword rules, no verification) |
| 8 | What changed since last period? | **No** — needs longitudinal |
| 9 | Which emerging topics are opportunities? | **No** — no trend signal |
| 10 | What should the business do next? | **Partly** — 4-stage memo, but templated, weak evidence link |

---

## Suggested next order (after the UX rethink Q wants)

1. `/api/v1/trends/{vertical}` + a `runs` table — unlocks Q3, Q8, "what changed", the executive home
2. `metric_definitions.md` — formula / normalization / limitations for every metric (§25)
3. Opportunity Engine v2 — real 0–100 score from (trend × gap × intent × competition) with evidence links (§26–27)
4. Language-style outcome measurement (§13) — the Thailand-specific differentiator
5. Flesh out the 3 research docs + add `metric_definitions`, `data_model`, `query_universe` docs (§47)
6. `model_discovery.yml` + `data_quality.yml` workflows (§39–40)
7. Entity graph + more of the §35 tables, once the above needs them
