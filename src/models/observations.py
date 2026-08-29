from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Provenance taxonomy (Phase 0 remediation)
# ---------------------------------------------------------------------------
# Previously a single ``engine_provider`` field was forced onto a narrow Literal
# that did not include Serper or Tavily, so those engines mislabelled themselves
# as "google_gemini" / "perplexity". Provenance is now split into orthogonal
# facts so every observation can be traced back to what actually produced it.
#
#   provider        - the concrete service that was called
#   model_name      - the model / endpoint identifier within that service
#   answer_surface  - the *kind* of result, so analytics never compares a
#                     generative recommendation rank against a SERP position

Provider = Literal["google_genai", "openrouter", "serper", "tavily", "mock"]

AnswerSurface = Literal[
    "generative_answer",  # an LLM answered a consumer question (Gemini, OpenRouter)
    "organic_serp",  # ranked organic search results (Serper)
    "web_retrieval",  # retrieved documents / citations only (Tavily)
    "synthetic",  # deterministic mock, no external call
]

ParseStatus = Literal[
    "ok",  # structured output parsed and validated
    "no_structured_output",  # provider returned prose with no parsable block
    "parse_error",  # a structured block was found but could not be parsed
    "not_applicable",  # engine does not use LLM structured output
]


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

    # --- provenance ---
    provider: Provider
    model_name: str
    answer_surface: AnswerSurface
    grounding_enabled: bool = True
    run_id: str | None = None
    prompt_version: str | None = None
    retry_count: int = 0

    # --- payload ---
    response_raw_text: str
    response_latency_ms: int
    token_count: int | None = None
    parse_status: ParseStatus = "not_applicable"
    brand_mentions: list[BrandMentionDetail] = Field(default_factory=list)
    citations: list[CitationSource] = Field(default_factory=list)
