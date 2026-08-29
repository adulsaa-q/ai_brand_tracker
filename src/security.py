# src/security.py
"""API authentication + basic abuse protection.

Phase 3 remediation: every endpoint was unauthenticated and there was no
concurrency or daily cap on paid-engine scans.

Deployment modes (chosen by env, read per-request so tests can override):

  AIBT_API_KEYS        comma-separated accepted keys. If empty -> "open" mode
                       (writes allowed, but /health reports auth="open" and a
                       warning is logged). If set -> writes require a valid key.
  AIBT_REQUIRE_AUTH    "true" -> read endpoints also require a key.
  AIBT_MAX_CONCURRENT_SCANS   default 2
  AIBT_MAX_RUNS_PER_DAY       default 200
"""

from __future__ import annotations

import os
import threading
from datetime import date

from fastapi import Header, HTTPException

from src.logger import get_logger

logger = get_logger("security")

_warned_open = False


def _configured_keys() -> set[str]:
    raw = os.getenv("AIBT_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def auth_mode() -> str:
    return "enforced" if _configured_keys() else "open"


def _check(provided: str | None) -> None:
    global _warned_open
    keys = _configured_keys()
    if not keys:
        if not _warned_open:
            logger.warning("AIBT_API_KEYS not set - API is running in OPEN mode (no authentication)")
            _warned_open = True
        return
    token = None
    if provided:
        token = provided[7:].strip() if provided.lower().startswith("bearer ") else provided.strip()
    if token not in keys:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


def require_write_auth(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    _check(x_api_key or authorization)


def require_read_auth(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    if os.getenv("AIBT_REQUIRE_AUTH", "").lower() == "true":
        _check(x_api_key or authorization)


class ScanLimiter:
    """In-process concurrency + daily-count guard for scan runs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = 0
        self._day = date.today()
        self._count_today = 0

    @property
    def max_concurrent(self) -> int:
        return int(os.getenv("AIBT_MAX_CONCURRENT_SCANS", "2"))

    @property
    def max_per_day(self) -> int:
        return int(os.getenv("AIBT_MAX_RUNS_PER_DAY", "200"))

    def acquire(self) -> None:
        with self._lock:
            today = date.today()
            if today != self._day:
                self._day, self._count_today = today, 0
            if self._running >= self.max_concurrent:
                raise HTTPException(status_code=429, detail="Too many concurrent scans; retry shortly")
            if self._count_today >= self.max_per_day:
                raise HTTPException(status_code=429, detail="Daily scan quota reached")
            self._running += 1
            self._count_today += 1

    def release(self) -> None:
        with self._lock:
            self._running = max(0, self._running - 1)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "max_concurrent": self.max_concurrent,
                "count_today": self._count_today,
                "max_per_day": self.max_per_day,
            }


scan_limiter = ScanLimiter()
