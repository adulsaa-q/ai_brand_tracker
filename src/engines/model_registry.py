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
        free_models = []
        for m in self.fetch_available_models():
            pricing = m.get("pricing", {})
            try:
                prompt_price = float(pricing.get("prompt", 0))
                completion_price = float(pricing.get("completion", 0))
            except (TypeError, ValueError):
                continue
            if (prompt_price == 0.0 and completion_price == 0.0) or ":free" in m.get("id", ""):
                free_models.append(
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "context_length": m.get("context_length"),
                        "description": m.get("description", ""),
                        "is_free": True,
                    }
                )
        return free_models
