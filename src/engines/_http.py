# src/engines/_http.py
"""Shared provider-call reliability policy.

Phase 2 remediation: each engine had its own ad-hoc ``urllib.request.urlopen``
with a bare timeout and no retry. Transient failures (429, 5xx, connection
resets) killed a whole scan query. This module centralises:

  - a single timeout default
  - bounded exponential backoff, ONLY for retryable classes
    (429, 5xx, timeout, connection error) - never for 4xx / auth / bad JSON
  - typed errors so the runner can categorise failures
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from src.exceptions import EngineError, RateLimitExceededError
from src.logger import get_logger

logger = get_logger("engine.http")

DEFAULT_TIMEOUT = 20
MAX_RETRIES = 2
BACKOFF_BASE = 1.5


def _sleep(attempt: int) -> None:
    time.sleep(BACKOFF_BASE**attempt)


def request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    method: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    engine: str = "http",
    max_retries: int = MAX_RETRIES,
) -> tuple[dict[str, Any], int]:
    """Return (parsed_json, retry_count). Raises typed EngineError on failure."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8")), attempt
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 429:
                if attempt < max_retries:
                    logger.warning("%s 429, retry %d/%d", engine, attempt + 1, max_retries)
                    _sleep(attempt)
                    continue
                raise RateLimitExceededError(f"{engine} rate limited", {"engine": engine}) from exc
            if 500 <= exc.code < 600 and attempt < max_retries:
                logger.warning("%s HTTP %d, retry %d/%d", engine, exc.code, attempt + 1, max_retries)
                _sleep(attempt)
                continue
            raise EngineError(f"{engine} HTTP {exc.code}", {"engine": engine, "status": exc.code}) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_exc = exc
            if attempt < max_retries:
                logger.warning("%s transport error (%s), retry %d/%d", engine, exc, attempt + 1, max_retries)
                _sleep(attempt)
                continue
            raise EngineError(f"{engine} transport error: {exc}", {"engine": engine}) from exc
        except json.JSONDecodeError as exc:
            raise EngineError(f"{engine} returned non-JSON body", {"engine": engine}) from exc

    raise EngineError(f"{engine} failed after retries: {last_exc}", {"engine": engine})


def retry_call(fn: Callable[[], Any], *, engine: str, max_retries: int = MAX_RETRIES) -> tuple[Any, int]:
    """Retry a callable (e.g. an SDK call) on generic exceptions. Returns (result, retry_count)."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn(), attempt
        except Exception as exc:  # SDK exception taxonomy varies; treat as retryable once
            last_exc = exc
            if attempt < max_retries:
                logger.warning("%s call failed (%s), retry %d/%d", engine, exc, attempt + 1, max_retries)
                _sleep(attempt)
                continue
    raise EngineError(f"{engine} call failed after retries: {last_exc}", {"engine": engine}) from last_exc
