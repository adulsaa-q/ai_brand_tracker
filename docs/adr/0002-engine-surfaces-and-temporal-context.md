# ADR 0002 — Answer surfaces, and where temporal context lives

**Status:** Accepted · **Date:** 2026-08-29 · **Phase:** 2 remediation

## Answer surfaces

Engines return fundamentally different signals:

| provider | `answer_surface` | what `rank` means |
| --- | --- | --- |
| google_genai, openrouter | `generative_answer` | position in the model's recommendation |
| serper | `organic_serp` | Google organic result position |
| tavily | `web_retrieval` | (no rank) brand appeared in a retrieved doc |
| mock | `synthetic` | fabricated, demo only |

**Decision:** Share of Voice / Net Recommendation Score are *generative-answer*
concepts. `MarketMetricsEngine.build_report` computes metrics **per surface** and
the headline `brands` / `total_queries` use `generative_answer` only
(`primary_surface`). A run with no generative surface (e.g. a pure mock or
SERP-only run) falls back to `all_surfaces_combined` and says so. The full
per-surface breakdown is always in `metrics.by_surface`.

Analytics never averages a SERP position against a generative rank.

## Temporal context

`ThailandTemporalEngine.get_active_events()` is evaluated once per run and stored
at **run grain** (`result.active_events`, and the run's row set shares one
timestamp window). It is deliberately **not** injected into control-set query
text: the 30 invariant queries must stay byte-identical across runs for
longitudinal comparison. A single scan never spans an event boundary, so
run-grain is the correct place for this fact. Slicing "how did SoV look during
11.11" is done by filtering runs whose `active_events` contains that event.
