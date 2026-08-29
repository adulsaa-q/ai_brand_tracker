# Security posture

Phase 3 baseline. This is an internal / single-tenant analytics tool, not a
public multi-tenant SaaS. The controls below match that.

## Authentication & authorization

| env | effect |
| --- | --- |
| `AIBT_API_KEYS` | comma-separated accepted keys. **Unset = OPEN mode**: writes are allowed, `/api/v1/health` reports `auth_mode: "open"`, and a warning is logged. Set it in any shared/deployed environment. |
| `AIBT_REQUIRE_AUTH=true` | read endpoints also require a key |

Keys are checked via `X-API-Key:` or `Authorization: Bearer <key>` by a central
FastAPI dependency (`src/security.py`) — never hardcoded. Write endpoints
(`POST /verticals`, `POST /scan`) always carry `require_write_auth`.

## Abuse / cost protection

- `POST /scan` `count` is bounded `1..200` (Pydantic).
- `ScanLimiter`: `AIBT_MAX_CONCURRENT_SCANS` (default 2) and
  `AIBT_MAX_RUNS_PER_DAY` (default 200) → `429` when exceeded.
- Unknown vertical → `404` before any engine is created (no wasted paid calls).
- Unknown engine / bad params → `422` before the background task is queued.

## CORS

`AIBT_ALLOWED_ORIGINS` (comma-separated). Unset → `*` with a logged warning.
`allow_credentials` is always `False`; methods limited to GET/POST/OPTIONS.

## Bring-your-own provider key (OpenRouter etc.)

Provider API keys are **never stored server-side**. Three ways to supply one, in
order of precedence:

1. `X-Provider-Key` request header on `POST /api/v1/scan` and `GET /api/v1/models`
   — used to build the engine for that one run, then dropped. It is never
   logged, never written to `tasks_state`, and never written to the run summary.
   Only a boolean `byok: true/false` is recorded.
2. Browser `localStorage` (`aibt_openrouter_key`) set via the dashboard's *API
   settings* — stays in that browser, sent only as the header above.
3. `OPENROUTER_API_KEY` env var — the CLI / server default.

`GET /api/v1/models?provider=openrouter` returns the **live** free-model list
(the free tier changes often, so it is fetched fresh every call, never cached to
disk).

## Untrusted content

Treat as untrusted: the consumer query text, provider responses, retrieved web
pages, and citation content.

- The runner never executes provider output; it only parses a JSON block and
  validates every field against `BrandMentionDetail` (unknown enum values are
  coerced to safe defaults, not trusted).
- Retrieved web-page content (Tavily `content`) is used only for substring brand
  detection. It is **not** concatenated into any LLM prompt.
- The Gemini JSON-repair prompt echoes back only the model's *own* previous
  output (truncated), never third-party retrieved text.
- Secrets: API keys are read from env at call time, kept in `SecretStr` where
  surfaced (`src/config.py`), and never placed in `EngineError` details or logs.

## Known gaps (tracked for later phases)

- No per-key rate limiting or audit log of who triggered which scan.
- `tasks_state` is in-process only (lost on restart); no persistent job store.
- No TLS termination in-app (expected to sit behind a reverse proxy).
