# Architecture & project flow

Diagrams render on GitHub. The code is the source of truth; if a diagram
disagrees, the code wins.

- Storage decision: [ADR 0001](adr/0001-single-analytical-store.md)
- Answer surfaces & temporal context: [ADR 0002](adr/0002-engine-surfaces-and-temporal-context.md)
- Per-feature status: [STATUS.md](STATUS.md)
- Security posture: [../SECURITY.md](../SECURITY.md)

---

## 1. System map

```mermaid
flowchart TD
    CLI["CLI<br/>python -m src.cli"]
    WEB["Web dashboard<br/>dashboard/web/index.html"]
    ST["Streamlit view<br/>dashboard/app.py"]

    API["FastAPI src/api.py :8000<br/>src/security.py auth + ScanLimiter"]
    WEB -->|"POST /scan, GET /progress, GET /metrics"| API
    CLI --> RUN
    API -->|BackgroundTask| RUN

    RUN["run_intelligence_pipeline<br/>src/runner.py — assigns run_id UUID"]
    GEN["QueryUniverseGenerator<br/>config/entities.yaml + control_benchmark_set.yaml + thai_personas.yaml"]
    FOCAL["resolve_focal_brand<br/>src/brands.py id / name / alias"]
    FACT["EngineFactory<br/>src/engines/factory.py"]
    RUN --> GEN --> FACT
    RUN --> FOCAL

    MOCK["mock — synthetic<br/>SHA-256 seeded"]
    GEM["gemini — generative_answer<br/>+ Google Search grounding"]
    OR["openrouter — generative_answer<br/>model from live free list"]
    SERP["serper — organic_serp"]
    TAV["tavily — web_retrieval"]
    FACT --> MOCK
    FACT --> GEM
    FACT --> OR
    FACT --> SERP
    FACT --> TAV

    SHARED["_http.py retry/backoff 429-5xx-timeout only<br/>_parsing.py parse -> ParseStatus<br/>prompts.py versioned registry<br/>ids.py UUID observation ids"]

    OBS["RawObservation<br/>provider · answer_surface · parse_status<br/>prompt_version · retry_count · run_id"]
    MOCK --> OBS
    GEM --> OBS
    OR --> OBS
    SERP --> OBS
    TAV --> OBS

    DUCK[("DuckDB star schema<br/>dim_brand · dim_query<br/>fact_observation · fact_brand_mention · fact_citation<br/>every fact row tagged run_id")]
    OBS -->|insert| DUCK

    REPO["AnalyticsRepository.load_observations(run_id)<br/>canonical read — analytics never use the in-memory list"]
    DUCK --> REPO

    MET["MarketMetrics.build_report<br/>SoV / NRS per answer_surface<br/>headline = generative_answer only"]
    OPP["OpportunityFinder — 4-stage memo"]
    CIT["CitationInfluence"]
    CLM["ClaimIntelligence"]
    LAG["InformationLag — grounding rate only"]
    REPO --> MET
    REPO --> OPP
    REPO --> CIT
    REPO --> CLM
    REPO --> LAG

    OUT["atomic write<br/>data/run_ID.json<br/>data/latest_run_summary_VERTICAL.json"]
    MET --> OUT
    OPP --> OUT
    CIT --> OUT
    CLM --> OUT
    LAG --> OUT

    API -->|"GET /metrics, GET /export"| OUT
    ST -->|reads| OUT
    OUT -->|adaptApiMetrics| WEB
```

---

## 2. Scan runtime sequence (web dashboard to live data)

```mermaid
sequenceDiagram
    autonumber
    actor U as Analyst
    participant W as index.html
    participant A as FastAPI
    participant L as ScanLimiter
    participant P as pipeline
    participant D as DuckDB

    U->>W: pick vertical + engine + model, click Run Scan
    W->>A: POST /api/v1/scan (X-API-Key, X-Provider-Key, model_name)
    A->>A: validate count 1..200, engine, vertical exists else 404
    A->>L: acquire — 429 if concurrency or daily quota exceeded
    A-->>W: 200 task_id, data_mode
    A->>P: queue background task

    loop every ~900ms until COMPLETED or FAILED
        W->>A: GET /api/v1/scan/{task_id}/progress
        A-->>W: status, progress_pct, completed/total, run_stats
    end

    P->>D: generate queries, persist dim_query
    loop each query
        P->>P: engine.observe — EngineError increments provider_errors
        P->>D: insert_observation — failure increments persistence_failures
    end
    P->>P: if 0 persisted then raise (task FAILED, no fabricated insight)
    P->>D: AnalyticsRepository.load_observations(run_id)
    P->>P: build_report, opportunities, citations, claims, lag
    P->>P: atomic write summary files
    P->>L: release

    W->>A: GET /api/v1/metrics/{vertical}
    A-->>W: full run summary
    W->>W: adaptApiMetrics then renderAll; banner LIVE / SYNTHETIC / ERROR
```

---

## 3. Data model (star schema)

```mermaid
erDiagram
    dim_brand ||--o{ fact_brand_mention : brand_id
    dim_query ||--o{ fact_observation : query_id
    dim_query ||--o{ fact_brand_mention : query_id
    fact_observation ||--o{ fact_brand_mention : observation_id
    fact_observation ||--o{ fact_citation : observation_id

    dim_brand {
        varchar brand_id PK
        varchar name
        varchar vertical
        boolean is_focal_brand
    }
    dim_query {
        varchar query_id PK
        varchar text_th
        varchar vertical
        varchar category
        boolean is_control_set
    }
    fact_observation {
        varchar observation_id PK
        varchar run_id
        varchar query_id FK
        varchar provider
        varchar answer_surface
        varchar parse_status
        varchar prompt_version
        int retry_count
        int latency_ms
        int token_count
    }
    fact_brand_mention {
        varchar mention_id PK
        varchar observation_id FK
        varchar run_id
        varchar brand_id FK
        boolean mentioned
        int rank
        varchar sentiment
    }
    fact_citation {
        varchar citation_id PK
        varchar observation_id FK
        varchar run_id
        varchar domain
        varchar source_type
    }
```

---

## 4. Answer-surface taxonomy (why metrics do not mix engines)

```mermaid
flowchart LR
    Q["Thai consumer query"] --> G
    Q --> S
    Q --> T
    Q --> M

    G["gemini / openrouter"] --> GA["generative_answer<br/>rank = model recommendation"]
    S["serper"] --> OS["organic_serp<br/>rank = Google result position"]
    T["tavily"] --> WR["web_retrieval<br/>no rank, brand seen in a doc"]
    M["mock"] --> SY["synthetic<br/>fabricated, demo only"]

    GA --> H["build_report<br/>HEADLINE SoV / NRS = generative_answer only"]
    OS --> BS["by_surface breakdown<br/>kept, never averaged into the headline"]
    WR --> BS
    SY --> FB["fallback all_surfaces_combined<br/>labelled, when no generative surface"]
```

---

## 5. Bring-your-own-key and the live free-model list (OpenRouter)

OpenRouter's free tier changes constantly, so the model list is fetched live, not
hardcoded. API keys are never stored server-side — they travel per request and
are dropped after use.

```mermaid
flowchart TD
    K1["Browser localStorage<br/>aibt_openrouter_key<br/>(dashboard: API settings)"]
    K2["X-Provider-Key header<br/>(API callers, per request)"]
    K3["OPENROUTER_API_KEY env<br/>(CLI / server default)"]

    K1 --> API
    K2 --> API
    K3 --> CLI

    API["FastAPI"]
    CLI["python -m src.cli"]

    API -->|"GET /api/v1/models?provider=openrouter"| REG
    REG["OpenRouterModelRegistry.get_free_tier_candidates()<br/>live call to openrouter.ai/api/v1/models<br/>filter: pricing == 0 or id endswith :free"]
    REG -->|"[{id, name, context_length}]"| PICKER["dashboard model dropdown<br/>(shown when engine = openrouter)"]

    PICKER -->|"POST /scan {engine_type: openrouter, model_name}"| API
    API -->|"model_name + key (not logged, not persisted)"| FACTORY["EngineFactory.create(engine_type, model_name, api_key)"]
    FACTORY --> ENG["OpenRouterEngine"]
    ENG -.->|"observation records model_name + prompt_version, NEVER the key"| DUCK[("DuckDB")]
```

---

## 6. Remediation phase map (branch phase/0-4-remediation)

```mermaid
flowchart TD
    P0["Phase 0 Stop the bleeding<br/>UUID ids, provenance split, drop SQLite,<br/>fail-loud persistence, focal-brand identity,<br/>packaging/CI, test isolation, input bounds"]
    P1["Phase 1 Data integrity<br/>E2E reconciliation test, dim_query populated,<br/>deterministic mock, atomic writes, task pruning"]
    P2["Phase 2 Source of truth<br/>AnalyticsRepository DuckDB canonical,<br/>answer-surface separation, prompt registry,<br/>shared retry/backoff policy"]
    P3["Phase 3 Security baseline<br/>API-key auth open/enforced, ScanLimiter,<br/>CORS config, dependency health"]
    P4["Phase 4 Real dashboard<br/>index.html to API, LIVE/SYNTHETIC/NO-DATA states,<br/>custom workspace = create vertical + scan, docs"]

    P0 --> P1 --> P2 --> P3 --> P4
```
