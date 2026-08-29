# Archived planning documents

These were the planning lineage that produced the current system. They are kept
for history but are **superseded** — do not treat them as current.

| File | What it was | Superseded by |
| --- | --- | --- |
| `MASTER_BLUEPRINT_V3.md` | First "approved" spec (8 sections: gap analysis, query-universe math, provider tiers, metric formulas, DoD) | `../MASTER_PROMPT.md` (vision) + `../ARCHITECTURE.md` (built reality) + `../metric_definitions.md` (implemented formulas) |
| `UNIVERSAL_AI_PLATFORM_V4_BLUEPRINT.md` | "Zero-terminal" V4 — FastAPI + web UI + API contract + roadmap | Built: `src/api.py`, `dashboard/web/index.html`. Contract is now the README API table. |
| `V5_DELTA_BLUEPRINT.md` | Audit of the V4 blueprint vs the repo + 5-wave roadmap | Executed in the phase 0–5 remediation. Remaining gaps live in `../MASTER_PROMPT_COVERAGE.md`. |

The three overlapped heavily (each restated the v1 problems, the multi-vertical
vision, the DuckDB star schema, the five executive questions). That content now
lives in exactly one place each:

- **Why / what it should become** → `../MASTER_PROMPT.md`
- **What exists now** → `../ARCHITECTURE.md`, `../STATUS.md`, `../adr/`
- **What's left** → `../MASTER_PROMPT_COVERAGE.md`
- **Legacy v1 audit** → `../FORENSIC_AUDIT.md`
- **Metric formulas** → `../metric_definitions.md`
