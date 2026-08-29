# src/api.py
from __future__ import annotations

import csv
import io
import json
import os
import sys
import threading
import time
import uuid
from typing import Any, Literal

import yaml
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logger import get_logger
from src.runner import run_intelligence_pipeline
from src.security import auth_mode, require_read_auth, require_write_auth, scan_limiter

logger = get_logger("api")

# Configurable so tests never mutate the real config file.
ENTITIES_PATH = os.getenv("ENTITIES_PATH", "config/entities.yaml")
DATA_DIR = os.getenv("DATA_DIR", "data")
MAX_TASK_HISTORY = 100

app = FastAPI(
    title="Thailand AI Market & Decision Intelligence API",
    description="AI Share of Voice & Market Intelligence Platform",
    version="5.0.0",
)


def _allowed_origins() -> list[str]:
    raw = os.getenv("AIBT_ALLOWED_ORIGINS", "").strip()
    if not raw:
        logger.warning("AIBT_ALLOWED_ORIGINS not set - CORS allows all origins")
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

tasks_state: dict[str, dict[str, Any]] = {}
tasks_lock = threading.Lock()


class BrandInput(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(min_length=1, max_length=120)
    aliases: list[str] = Field(default_factory=list, max_length=20)
    official_domains: list[str] = Field(default_factory=list, max_length=20)
    is_focal_brand: bool = False


class VerticalCreateRequest(BaseModel):
    vertical_id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_]+$")
    name_th: str = Field(min_length=1, max_length=200)
    name_en: str = Field(min_length=1, max_length=200)
    focal_brand: str = Field(min_length=1, max_length=120)
    categories: list[str] = Field(default_factory=list, max_length=40)
    brands: list[BrandInput] = Field(default_factory=list, min_length=1, max_length=40)


class ScanTriggerRequest(BaseModel):
    vertical_id: str = Field("ecommerce_retail_th", min_length=2, max_length=64)
    engine_type: Literal["mock", "gemini", "openrouter", "tavily", "serper"] = "mock"
    count: int = Field(30, ge=1, le=200)
    include_control_set: bool = True
    seed: int = Field(42, ge=0, le=2**31 - 1)


def _get_entities_config() -> dict[str, Any]:
    if os.path.exists(ENTITIES_PATH):
        with open(ENTITIES_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"verticals": []}
    return {"verticals": []}


def _save_entities_config(data: dict[str, Any]):
    parent = os.path.dirname(ENTITIES_PATH) or "."
    os.makedirs(parent, exist_ok=True)
    with open(ENTITIES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _prune_tasks_locked() -> None:
    if len(tasks_state) <= MAX_TASK_HISTORY:
        return
    finished = sorted(
        (t for t in tasks_state.values() if t.get("status") in ("COMPLETED", "FAILED")),
        key=lambda t: t.get("finished_at", 0),
    )
    for t in finished[: len(tasks_state) - MAX_TASK_HISTORY]:
        tasks_state.pop(t["task_id"], None)


def _run_scan_background_task(
    task_id: str, vertical_id: str, engine_type: str, count: int, seed: int, include_control: bool
):
    with tasks_lock:
        tasks_state[task_id]["status"] = "RUNNING"
        tasks_state[task_id]["started_at"] = time.time()

    def progress_callback(current: int, total: int, query_text: str):
        with tasks_lock:
            tasks_state[task_id].update(
                completed=current,
                total=total,
                progress_pct=round((current / total) * 100, 1) if total else 0.0,
                current_query=query_text,
            )

    try:
        result = run_intelligence_pipeline(
            vertical_id=vertical_id,
            count=count,
            seed=seed,
            engine_type=engine_type,
            include_control=include_control,
            progress_callback=progress_callback,
            entities_path=ENTITIES_PATH,
            output_dir=DATA_DIR,
        )
        with tasks_lock:
            tasks_state[task_id].update(
                status="COMPLETED",
                progress_pct=100.0,
                run_id=result.get("run_id"),
                data_mode=result.get("data_mode"),
                run_stats=result.get("run_stats"),
                result=result,
                finished_at=time.time(),
            )
            _prune_tasks_locked()
    except Exception as exc:
        logger.exception("Background task %s failed", task_id)
        with tasks_lock:
            tasks_state[task_id].update(
                status="FAILED",
                error=str(exc),
                error_type=type(exc).__name__,
                finished_at=time.time(),
            )
            _prune_tasks_locked()
    finally:
        scan_limiter.release()


# ---------------------------------------------------------------- REST


@app.get("/api/v1/health")
def get_health():
    """Liveness is always 'ok' if this responds. 'dependencies' is the real check."""
    deps: dict[str, Any] = {}
    try:
        cfg = _get_entities_config()
        deps["entities_config"] = "ok" if cfg.get("verticals") else "empty"
    except Exception as exc:  # noqa: BLE001 - health must never raise
        deps["entities_config"] = f"error: {exc}"
    try:
        from src.storage import DuckDBStore

        DuckDBStore(db_path=os.path.join(DATA_DIR, "intelligence.duckdb")).count_rows("dim_brand")
        deps["duckdb"] = "ok"
    except Exception as exc:  # noqa: BLE001
        deps["duckdb"] = f"error: {exc}"

    healthy = all(v == "ok" or v == "empty" for v in deps.values())
    return {
        "status": "healthy" if healthy else "degraded",
        "liveness": "ok",
        "version": "5.0.0",
        "auth_mode": auth_mode(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_tasks": len([t for t in tasks_state.values() if t.get("status") == "RUNNING"]),
        "scan_limiter": scan_limiter.snapshot(),
        "dependencies": deps,
    }


@app.get("/api/v1/verticals", dependencies=[Depends(require_read_auth)])
def get_verticals():
    return _get_entities_config().get("verticals", [])


@app.post("/api/v1/verticals", dependencies=[Depends(require_write_auth)])
def create_vertical(req: VerticalCreateRequest):
    config = _get_entities_config()
    verticals = config.setdefault("verticals", [])
    payload = req.model_dump()
    for idx, v in enumerate(verticals):
        if v["vertical_id"] == req.vertical_id:
            verticals[idx] = payload
            _save_entities_config(config)
            return {"status": "UPDATED", "vertical": payload}
    verticals.append(payload)
    _save_entities_config(config)
    return {"status": "CREATED", "vertical": payload}


@app.post("/api/v1/scan", dependencies=[Depends(require_write_auth)])
def trigger_scan(req: ScanTriggerRequest, background_tasks: BackgroundTasks):
    known = {v["vertical_id"] for v in _get_entities_config().get("verticals", [])}
    if req.vertical_id not in known:
        raise HTTPException(status_code=404, detail=f"Unknown vertical: {req.vertical_id}")

    scan_limiter.acquire()  # raises 429 on concurrency / daily-quota limit
    task_id = f"scan_{uuid.uuid4().hex[:8]}"
    with tasks_lock:
        tasks_state[task_id] = {
            "task_id": task_id,
            "vertical_id": req.vertical_id,
            "engine_type": req.engine_type,
            "data_mode": "synthetic" if req.engine_type == "mock" else "live",
            "status": "QUEUED",
            "progress_pct": 0.0,
            "completed": 0,
            "total": req.count,
            "current_query": "Initializing observation engines...",
            "created_at": time.time(),
            "result": None,
            "error": None,
        }
    background_tasks.add_task(
        _run_scan_background_task,
        task_id=task_id,
        vertical_id=req.vertical_id,
        engine_type=req.engine_type,
        count=req.count,
        seed=req.seed,
        include_control=req.include_control_set,
    )
    data_mode = "synthetic" if req.engine_type == "mock" else "live"
    return {"task_id": task_id, "status": "QUEUED", "vertical_id": req.vertical_id, "data_mode": data_mode}


@app.get("/api/v1/scan/{task_id}/progress", dependencies=[Depends(require_read_auth)])
def get_scan_progress(task_id: str):
    with tasks_lock:
        if task_id not in tasks_state:
            raise HTTPException(status_code=404, detail="Task ID not found")
        return tasks_state[task_id]


@app.get("/api/v1/metrics/{vertical_id}", dependencies=[Depends(require_read_auth)])
def get_vertical_metrics(vertical_id: str):
    path = os.path.join(DATA_DIR, f"latest_run_summary_{vertical_id}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "vertical_id": vertical_id,
        "data_mode": "none",
        "status": "PENDING_SCAN",
        "metrics": {"total_queries": 0, "brands": []},
        "opportunities": [],
        "citations_analysis": {"total_citations": 0, "domain_rankings": []},
        "claims_audit": [],
        "information_lag": {"grounded_rate_pct": 0.0},
    }


@app.get("/api/v1/export/{vertical_id}", dependencies=[Depends(require_read_auth)])
def export_vertical_data(vertical_id: str, format: str = "csv"):
    path = os.path.join(DATA_DIR, f"latest_run_summary_{vertical_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No analytical data found for this vertical.")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if format == "json":
        return JSONResponse(content=data)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Rank", "Brand", "Share_of_Voice_Pct", "Average_Rank", "Net_Sentiment_Score", "Net_Recommendation_Score"]
    )
    for idx, b in enumerate(data.get("metrics", {}).get("brands", []), start=1):
        writer.writerow(
            [
                idx,
                b.get("brand"),
                b.get("share_of_voice_pct"),
                b.get("average_rank"),
                b.get("net_sentiment_score"),
                b.get("net_recommendation_score"),
            ]
        )
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ai_market_intelligence_{vertical_id}.csv"},
    )


# ---------------------------------------------------------------- static web
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "web"))
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    def serve_index():
        index_file = os.path.join(web_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Web UI directory found but index.html is missing."}
