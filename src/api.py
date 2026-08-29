# src/api.py
from __future__ import annotations

import csv
import io
import os
import sys
import threading
import time
import uuid
from typing import Any

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logger import get_logger
from src.runner import run_intelligence_pipeline

logger = get_logger("api")

app = FastAPI(
    title="Thailand AI Market & Decision Intelligence API",
    description="Universal Production-Grade AI Share of Voice & Market Intelligence Platform",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-Memory Background Tasks State Store
tasks_state: dict[str, dict[str, Any]] = {}
tasks_lock = threading.Lock()


class BrandInput(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    official_domains: list[str] = Field(default_factory=list)
    is_focal_brand: bool = False


class VerticalCreateRequest(BaseModel):
    vertical_id: str
    name_th: str
    name_en: str
    focal_brand: str
    categories: list[str] = Field(default_factory=list)
    brands: list[BrandInput] = Field(default_factory=list)


class ScanTriggerRequest(BaseModel):
    vertical_id: str = "ecommerce_retail_th"
    engine_type: str = "mock"  # "mock" | "gemini" | "tavily" | "openrouter"
    count: int = 30
    include_control_set: bool = True
    seed: int = 42


def _get_entities_config() -> dict[str, Any]:
    entities_path = "config/entities.yaml"
    if os.path.exists(entities_path):
        with open(entities_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"verticals": []}
    return {"verticals": []}


def _save_entities_config(data: dict[str, Any]):
    os.makedirs("config", exist_ok=True)
    with open("config/entities.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _run_scan_background_task(
    task_id: str, vertical_id: str, engine_type: str, count: int, seed: int, include_control: bool
):
    with tasks_lock:
        tasks_state[task_id]["status"] = "RUNNING"
        tasks_state[task_id]["started_at"] = time.time()

    def progress_callback(current: int, total: int, query_text: str):
        with tasks_lock:
            tasks_state[task_id]["completed"] = current
            tasks_state[task_id]["total"] = total
            tasks_state[task_id]["progress_pct"] = round((current / total) * 100, 1)
            tasks_state[task_id]["current_query"] = query_text

    try:
        result = run_intelligence_pipeline(
            vertical_id=vertical_id,
            count=count,
            seed=seed,
            engine_type=engine_type,
            include_control=include_control,
            progress_callback=progress_callback,
        )
        with tasks_lock:
            tasks_state[task_id]["status"] = "COMPLETED"
            tasks_state[task_id]["progress_pct"] = 100.0
            tasks_state[task_id]["completed"] = count
            tasks_state[task_id]["total"] = count
            tasks_state[task_id]["result"] = result
            tasks_state[task_id]["finished_at"] = time.time()
    except Exception as e:
        logger.error(f"Background task {task_id} failed: {e}")
        with tasks_lock:
            tasks_state[task_id]["status"] = "FAILED"
            tasks_state[task_id]["error"] = str(e)
            tasks_state[task_id]["finished_at"] = time.time()


# ==========================================
# REST ENDPOINTS
# ==========================================


@app.get("/api/v1/health")
def get_health():
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_tasks": len([t for t in tasks_state.values() if t.get("status") == "RUNNING"]),
    }


@app.get("/api/v1/verticals")
def get_verticals():
    config = _get_entities_config()
    return config.get("verticals", [])


@app.post("/api/v1/verticals")
def create_vertical(req: VerticalCreateRequest):
    config = _get_entities_config()
    verticals = config.get("verticals", [])

    # Check if vertical already exists
    for idx, v in enumerate(verticals):
        if v["vertical_id"] == req.vertical_id:
            verticals[idx] = req.model_dump()
            _save_entities_config(config)
            return {"status": "UPDATED", "vertical": req.model_dump()}

    new_vertical = req.model_dump()
    verticals.append(new_vertical)
    config["verticals"] = verticals
    _save_entities_config(config)
    return {"status": "CREATED", "vertical": new_vertical}


@app.post("/api/v1/scan")
def trigger_scan(req: ScanTriggerRequest, background_tasks: BackgroundTasks):
    task_id = f"scan_{uuid.uuid4().hex[:8]}"
    with tasks_lock:
        tasks_state[task_id] = {
            "task_id": task_id,
            "vertical_id": req.vertical_id,
            "engine_type": req.engine_type,
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

    return {"task_id": task_id, "status": "QUEUED", "vertical_id": req.vertical_id}


@app.get("/api/v1/scan/{task_id}/progress")
def get_scan_progress(task_id: str):
    with tasks_lock:
        if task_id not in tasks_state:
            raise HTTPException(status_code=404, detail="Task ID not found")
        return tasks_state[task_id]


@app.get("/api/v1/metrics/{vertical_id}")
def get_vertical_metrics(vertical_id: str):
    summary_path = f"data/latest_run_summary_{vertical_id}.json"
    if os.path.exists(summary_path):
        import json

        with open(summary_path, encoding="utf-8") as f:
            return json.load(f)

    # Fallback to general summary if available
    general_summary = "data/latest_run_summary.json"
    if os.path.exists(general_summary):
        import json

        with open(general_summary, encoding="utf-8") as f:
            data = json.load(f)
            if data.get("vertical_id") == vertical_id:
                return data

    # Return empty structured schema
    return {
        "vertical_id": vertical_id,
        "metrics": {"total_queries": 0, "brands": []},
        "opportunities": [],
        "citations_analysis": {"total_citations": 0, "domains": []},
        "claims_audit": [],
        "information_lag": {"freshness_status": "PENDING_SCAN"},
    }


@app.get("/api/v1/export/{vertical_id}")
def export_vertical_data(vertical_id: str, format: str = "csv"):
    summary_path = f"data/latest_run_summary_{vertical_id}.json"
    if not os.path.exists(summary_path):
        summary_path = "data/latest_run_summary.json"

    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="No analytical data found for export.")

    import json

    with open(summary_path, encoding="utf-8") as f:
        data = json.load(f)

    if format == "json":
        return JSONResponse(content=data)

    # Export CSV format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Rank", "Brand", "Share_of_Voice_Pct", "Average_Rank", "Net_Sentiment_Score", "Net_Recommendation_Score"]
    )

    for idx, b in enumerate(data.get("metrics", {}).get("brands", [])):
        writer.writerow(
            [
                idx + 1,
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


# ==========================================
# STATIC WEB DASHBOARD MOUNT
# ==========================================
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboard", "web"))
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    def serve_index():
        index_file = os.path.join(web_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Web UI directory found but index.html is missing."}
