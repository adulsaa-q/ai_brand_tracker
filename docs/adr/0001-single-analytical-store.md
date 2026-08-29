# ADR 0001 — Single analytical store (DuckDB)

**Status:** Accepted · **Date:** 2026-08-29 · **Phase:** 0 remediation

## Context

The codebase carried two persistence layers with near-identical star schemas:

- `DuckDBStore` (`data/intelligence.duckdb`) — written on every observation, but
  never read back by analytics, the API, or the dashboards.
- `SQLiteStore` (`data/intelligence.db`) — the runner called
  `sqlite_store.insert_raw_observation(...)`, a method that **did not exist**.
  Every call raised `AttributeError`, was swallowed by a broad `except` in the
  runner, and logged as a warning. SQLite therefore only ever held `dim_brand`
  rows; `fact_observation` / `fact_brand_mention` were always empty.

No component required transactional/OLTP semantics. `tasks_state` in the API is
in-memory; Streamlit reads a JSON summary file, not a database.

## Decision

Keep **DuckDB as the single analytical source of truth**. Delete `SQLiteStore`
and remove the dual-write from the runner and migration script.

`fact_observation` / `fact_brand_mention` / `fact_citation` gain a `run_id`
column so a single end-to-end run is traceable end to end. `dim_query` is now
actually populated by the runner.

## Consequences

- One schema to evolve, one write path to test.
- Analytics can (Phase 2) read canonical data from DuckDB via `fetch_df`.
- If a future feature genuinely needs OLTP (multi-writer, row locking), that is a
  new ADR — not a reason to resurrect the unused SQLite layer.
- Local `data/*.db` / `data/*.duckdb` are gitignored dev artifacts; deleting them
  to pick up the new schema is safe.
