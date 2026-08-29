import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.logger import get_logger

logger = get_logger("engine.registry")


class OpenRouterModelRegistry:
    """Discovers free / low-cost models on OpenRouter.

    Phase 0 remediation: ``benchmark_thai_competency`` was removed. It returned
    hardcoded scores (92.5 / 98.0 / "S-TIER") that looked like a real
    measurement. A genuine Thai-competency eval belongs in Phase 2.
    """

    ENDPOINT = "https://openrouter.ai/api/v1/models"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    def fetch_available_models(self) -> list[dict[str, Any]]:
        headers = {"User-Agent": "Thailand-AI-Market-Intelligence/5.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(self.ENDPOINT, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8")).get("data", [])
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("Could not fetch OpenRouter models: %s", exc)
            return []

    def get_free_tier_candidates(self) -> list[dict[str, Any]]:
        """Live list of currently-free OpenRouter models.

        OpenRouter's free tier changes frequently, so this is always fetched, not
        cached to disk. Sorted by context length so the most capable free model
        is first.
        """
        free_models = []
        for m in self.fetch_available_models():
            pricing = m.get("pricing", {})
            try:
                prompt_price = float(pricing.get("prompt", 0))
                completion_price = float(pricing.get("completion", 0))
            except (TypeError, ValueError):
                continue
            is_free = (prompt_price == 0.0 and completion_price == 0.0) or ":free" in m.get("id", "")
            # keep only models that can emit text (skip image/audio-only endpoints)
            out_mods = (m.get("architecture") or {}).get("output_modalities")
            emits_text = (not out_mods) or ("text" in out_mods)
            if is_free and emits_text:
                free_models.append(
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "context_length": m.get("context_length") or 0,
                        "description": (m.get("description", "") or "")[:280],
                        "is_free": True,
                    }
                )
        free_models.sort(key=lambda x: x["context_length"], reverse=True)
        return free_models
