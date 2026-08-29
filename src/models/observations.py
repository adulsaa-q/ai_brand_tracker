from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BrandMentionDetail(BaseModel):
    brand_id: str
    brand_name: str
    mentioned: bool = True
    rank: int | None = Field(None, description="Recommendation rank (1 = top choice)")
    recommendation_intent: Literal[
        "strongly_recommended", "recommended", "neutral_mention", "not_recommended", "warning_or_caution"
    ] = "recommended"
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    key_strengths_mentioned: list[str] = Field(default_factory=list)
    key_weaknesses_mentioned: list[str] = Field(default_factory=list)
    price_or_deal_claims: list[str] = Field(default_factory=list)

class CitationSource(BaseModel):
    url: str | None = None
    domain: str
    title: str | None = None
    source_type: Literal["news", "blog", "marketplace", "social", "forum", "brand_official", "unknown"] = "unknown"
    authority_score: float = 0.5

class RawObservation(BaseModel):
    observation_id: str
    timestamp: str
    query_id: str
    query_text: str
    engine_provider: Literal["google_gemini", "openai_chatgpt", "anthropic_claude", "perplexity", "openrouter"]
    model_name: str
    grounding_enabled: bool = True
    response_raw_text: str
    response_latency_ms: int
    token_count: int | None = None
    brand_mentions: list[BrandMentionDetail] = Field(default_factory=list)
    citations: list[CitationSource] = Field(default_factory=list)
