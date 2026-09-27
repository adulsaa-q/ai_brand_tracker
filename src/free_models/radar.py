from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CATALOG_URL = "https://openrouter.ai/api/v1/models"


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


class FreeModelRadar:
    """Deterministic OpenRouter free-model catalog radar.

    The radar only reads the public catalog and never calls an LLM. It stores a
    curated registry plus immutable timestamped snapshots and reports additions
    or removals without changing Hermes routing.
    """

    def __init__(self, state_dir: str | Path = "data/free_models", api_key: str | None = None):
        self.state_dir = Path(state_dir)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    def fetch_catalog(self) -> list[dict[str, Any]]:
        headers = {"User-Agent": "Thailand-AI-Market-Intelligence/free-model-radar"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(CATALOG_URL, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenRouter catalog fetch failed: {exc}") from exc
        models = payload.get("data")
        if not isinstance(models, list):
            raise RuntimeError("OpenRouter catalog response has no data list")
        return models

    @staticmethod
    def curate(models: list[dict[str, Any]], min_context: int = 32_000) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        excluded = ("audio", "image", "embed", "rerank", "whisper", "flux", "sdxl", "lyria", "inkling", "content-safety")
        for model in models:
            model_id = str(model.get("id") or "")
            pricing = model.get("pricing") or {}
            try:
                free = float(pricing.get("prompt", 1)) == 0 and float(pricing.get("completion", 1)) == 0
            except (TypeError, ValueError):
                free = False
            if not model_id or not free or any(token in model_id.lower() for token in excluded):
                continue
            architecture = model.get("architecture") or {}
            modalities = architecture.get("output_modalities") or ["text"]
            if "text" not in modalities:
                continue
            context = int(model.get("context_length") or 0)
            if context < min_context:
                continue
            parameters = model.get("supported_parameters") or []
            result[model_id] = {
                "id": model_id,
                "name": model.get("name") or model_id,
                "context_length": context,
                "description": str(model.get("description") or "")[:400],
                "supported_parameters": sorted(str(p) for p in parameters),
                "tools": "tools" in parameters or "tool_choice" in parameters,
                "free": True,
            }
        return dict(sorted(result.items()))

    def run(self, min_context: int = 32_000) -> dict[str, Any]:
        catalog = self.fetch_catalog()
        candidates = self.curate(catalog, min_context=min_context)
        registry_path = self.state_dir / "registry.json"
        previous: dict[str, Any] = {}
        if registry_path.exists():
            try:
                previous = json.loads(registry_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                previous = {}
        old_models = previous.get("models", {})
        added = sorted(set(candidates) - set(old_models))
        removed = sorted(set(old_models) - set(candidates))
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        snapshot = {"fetched_at": now, "catalog_count": len(catalog), "models": candidates}
        snapshot_hash = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        _atomic_json(self.state_dir / "snapshots" / f"{now.replace(':', '').replace('-', '')}.json", snapshot)
        _atomic_json(registry_path, {"updated_at": now, "snapshot_hash": snapshot_hash, "models": candidates})
        return {"status": "changed" if added or removed else "unchanged", "added": added, "removed": removed,
                "count": len(candidates), "registry": str(registry_path), "updated_at": now}
