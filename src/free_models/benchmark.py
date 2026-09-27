from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_TASKS = [
    {"id": "reasoning", "prompt": "Solve this synthetic task. Return exactly: RESULT=42\nEXPLANATION=7*6.", "expected": "RESULT=42"},
    {"id": "patch_plan", "prompt": "For a Python function that returns the sum of a list, name two edge-case tests. Return exactly two lines beginning TEST=.", "expected": "TEST="},
]


def _post(model: str, api_key: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> tuple[dict[str, Any], float]:
    payload: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": 300, "temperature": 0}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(), headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/adulsaa-q/ai_brand_tracker",
        "X-Title": "Free Model Contractor Benchmark",
    })
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode()), time.monotonic() - started


def benchmark_model(model: str, api_key: str | None = None) -> dict[str, Any]:
    """Run harmless synthetic tests and return a registry-ready record."""
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is required for a live benchmark")
    record: dict[str, Any] = {"model": model, "provider": "openrouter", "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                              "status": "FAILED", "tasks": [], "tool_calling": False}
    for task in DEFAULT_TASKS:
        try:
            data, latency = _post(model, key, [{"role": "user", "content": task["prompt"]}])
            content = str((data.get("choices") or [{}])[0].get("message", {}).get("content") or "")
            record["tasks"].append({"id": task["id"], "passed": task["expected"] in content, "latency_seconds": round(latency, 3), "output": content[:1000]})
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
            record["tasks"].append({"id": task["id"], "passed": False, "error": str(exc)})
    try:
        data, latency = _post(model, key, [{"role": "user", "content": "Use the tool exactly once."}], tools=[{"type": "function", "function": {"name": "record_probe", "description": "Record a probe", "parameters": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}}}])
        message = (data.get("choices") or [{}])[0].get("message", {})
        record["tool_calling"] = bool(message.get("tool_calls"))
        record["tool_latency_seconds"] = round(latency, 3)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
        record["tool_error"] = str(exc)
    passed = sum(bool(t.get("passed")) for t in record["tasks"])
    record["score"] = round((passed / len(DEFAULT_TASKS)) * 70 + (30 if record["tool_calling"] else 0), 1)
    record["status"] = "APPROVED_FREE" if record["score"] >= 70 else "BENCHMARK_HOLD"
    return record


def save_benchmark(record: dict[str, Any], state_dir: str | Path = "data/free_models") -> Path:
    path = Path(state_dir) / "benchmarks" / f"{record['model'].replace('/', '__').replace(':', '_')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
