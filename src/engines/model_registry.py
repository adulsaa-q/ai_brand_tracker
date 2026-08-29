import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.logger import get_logger

logger = get_logger("engine.registry")

# Families that reliably work as plain chat-completions models on the free tier.
_CHAT_FAMILIES = (
    "llama",
    "deepseek",
    "qwen",
    "mistral",
    "mixtral",
    "gemma",
    "glm",
    "nemotron",
    "phi",
    "hermes",
    "openchat",
    "gpt-oss",
)
# Substrings that mark non-chat / restricted free endpoints.
_EXCLUDE = (
    "lyria",  # audio
    "inkling",  # "agentic harnesses only"
    "sdxl",
    "flux",
    "dall",
    "stable-diffusion",
    "whisper",
    "embed",
    "rerank",
    "vision-only",
    "-image",
)


class OpenRouterModelRegistry:
    """Discovers currently-free OpenRouter models and picks one that actually
    works for chat completions (the free tier changes constantly)."""

    ENDPOINT = "https://openrouter.ai/api/v1/models"
    CHAT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    # process-lifetime cache: {api_key_hash: model_id}
    _resolved: dict[str, str] = {}

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
        """Live list of currently-free models, sorted by context length."""
        free_models = []
        for m in self.fetch_available_models():
            mid = (m.get("id") or "").lower()
            pricing = m.get("pricing", {})
            try:
                free = float(pricing.get("prompt", 0)) == 0.0 and float(pricing.get("completion", 0)) == 0.0
            except (TypeError, ValueError):
                continue
            free = free or ":free" in mid
            out_mods = (m.get("architecture") or {}).get("output_modalities")
            emits_text = (not out_mods) or ("text" in out_mods)
            if free and emits_text and not any(x in mid for x in _EXCLUDE):
                free_models.append(
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "context_length": m.get("context_length") or 0,
                        "description": (m.get("description", "") or "")[:280],
                        "is_free": True,
                        "chat_family": any(f in mid for f in _CHAT_FAMILIES),
                    }
                )
        free_models.sort(key=lambda x: (x["chat_family"], x["context_length"]), reverse=True)
        return free_models

    def _probe(self, model_id: str) -> bool:
        if not self.api_key:
            return False
        req = urllib.request.Request(
            self.CHAT_ENDPOINT,
            data=json.dumps(
                {"model": model_id, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}
            ).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                json.loads(resp.read().decode("utf-8"))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.info("Free-model probe rejected %s: %s", model_id, exc)
            return False

    def resolve_working_free_model(self, max_probes: int = 5) -> str:
        """Return a free model id confirmed to answer a chat request.

        Result is cached for the process lifetime. Falls back to a stable
        well-known free id if nothing probes clean (or offline).
        """
        cache_key = (self.api_key or "anon")[-8:]
        if cache_key in self._resolved:
            return self._resolved[cache_key]

        fallback = "meta-llama/llama-3.3-70b-instruct:free"
        candidates = [m["id"] for m in self.get_free_tier_candidates() if m["chat_family"]]
        candidates = candidates or [m["id"] for m in self.get_free_tier_candidates()]

        for mid in candidates[:max_probes]:
            if self._probe(mid):
                logger.info("Resolved working free OpenRouter model: %s", mid)
                self._resolved[cache_key] = mid
                return mid

        logger.warning("No free model probed clean; using fallback %s", fallback)
        self._resolved[cache_key] = fallback
        return fallback
