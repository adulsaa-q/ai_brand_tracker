from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ThaiPersona(BaseModel):
    id: str
    name: str
    age_group: str
    location_type: Literal["bkk", "urban_province", "rural", "any"] = "any"
    budget_tier: Literal["budget", "value", "premium", "luxury"] = "value"
    tech_savviness: Literal["low", "medium", "high"] = "medium"
    primary_channels: list[str] = Field(default_factory=list)
    language_style: Literal["formal", "casual", "slang", "mixed_en_th"] = "casual"

class QueryDimension(BaseModel):
    vertical: str
    category: str
    intent: Literal["informational", "comparison", "recommendation", "deal_seeking", "troubleshooting", "trust_verification"]
    persona: ThaiPersona
    concern_points: list[str] = Field(default_factory=list)
    budget_limit_thb: float | None = None
    target_channel: str = "general"

class QueryInstance(BaseModel):
    id: str
    text_th: str
    dimension: QueryDimension
    is_control_set: bool = Field(default=False, description="Control set queries are constant over time")
    generated_at: str
    seed: int
