# src/logger.py
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for Enterprise Observability (2026 standard)."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """High-readability development console formatter."""

    COLORS = {
        logging.DEBUG: "\x1b[36m",  # Cyan
        logging.INFO: "\x1b[32m",  # Green
        logging.WARNING: "\x1b[33m",  # Yellow
        logging.ERROR: "\x1b[31m",  # Red
        logging.CRITICAL: "\x1b[41m",  # Red background
    }
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        msg = record.getMessage()
        return f"{color}[{time_str}] {record.levelname:<7} \x1b[1m[{record.name}]\x1b[0m {msg}{self.RESET}"


def get_logger(name: str = "app") -> logging.Logger:
    """Factory for structured enterprise logger."""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    app_env = os.getenv("APP_ENV", "development").lower()

    if app_env == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ColorFormatter())

    logger.addHandler(handler)
    logger.propagate = False
    return logger
