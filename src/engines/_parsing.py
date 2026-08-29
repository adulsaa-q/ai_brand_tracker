# src/engines/_parsing.py
"""Shared structured-output parsing for LLM observation engines.

Phase 0 remediation: engines used to do ``except Exception: pass`` around JSON
parsing, which turned a technical failure (model returned malformed JSON) into a
business fact (``brand_mentions=[]`` -> "brand never mentioned"). Parsing now
reports an explicit :class:`~src.models.observations.ParseStatus` so the runner
can count parse failures instead of silently absorbing them.
"""

from __future__ import annotations

import json
from typing import Any

from src.logger import get_logger
from src.models.observations import BrandMentionDetail, ParseStatus

logger = get_logger("engine.parsing")

_VALID_INTENTS = {
    "strongly_recommended",
    "recommended",
    "neutral_mention",
    "not_recommended",
    "warning_or_caution",
}
_VALID_SENTIMENT = {"positive", "neutral", "negative"}


def _extract_json_block(raw_text: str) -> str | None:
    if "```json" in raw_text:
        try:
            return raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            return None
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start != -1 and end > start:
        return raw_text[start : end + 1]
    return None


def _coerce_mention(m: dict[str, Any]) -> BrandMentionDetail | None:
    name = (m.get("brand_name") or m.get("brand") or "").strip()
    if not name:
        return None
    intent = m.get("recommendation_intent", "recommended")
    if intent not in _VALID_INTENTS:
        intent = "recommended"
    sentiment = m.get("sentiment", "neutral")
    if sentiment not in _VALID_SENTIMENT:
        sentiment = "neutral"
    rank = m.get("rank")
    if isinstance(rank, str) and rank.isdigit():
        rank = int(rank)
    if not isinstance(rank, int):
        rank = None
    return BrandMentionDetail(
        brand_id=name.lower().replace(" ", "_"),
        brand_name=name,
        mentioned=bool(m.get("mentioned", True)),
        rank=rank,
        recommendation_intent=intent,
        sentiment=sentiment,
        key_strengths_mentioned=list(m.get("key_strengths") or m.get("key_strengths_mentioned") or []),
        key_weaknesses_mentioned=list(m.get("key_weaknesses") or m.get("key_weaknesses_mentioned") or []),
        price_or_deal_claims=list(m.get("price_or_deal_claims") or []),
    )


def parse_brand_mentions(raw_text: str, *, query_id: str) -> tuple[list[BrandMentionDetail], ParseStatus]:
    """Parse a model's structured brand-mention block.

    Returns the parsed mentions and a status describing what happened. Never
    raises for malformed model output.
    """
    block = _extract_json_block(raw_text or "")
    if block is None:
        logger.warning("No structured JSON block in model output for query %s", query_id)
        return [], "no_structured_output"

    try:
        parsed = json.loads(block)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("JSON parse error for query %s: %s", query_id, exc)
        return [], "parse_error"

    if not isinstance(parsed, dict):
        return [], "parse_error"

    mentions: list[BrandMentionDetail] = []
    for m in parsed.get("brand_mentions", []):
        if not isinstance(m, dict):
            continue
        coerced = _coerce_mention(m)
        if coerced is not None:
            mentions.append(coerced)

    return mentions, "ok"
