from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class BrandEntity(BaseModel):
    id: str = Field(..., description="Unique slug (e.g. shopee, konvy, kbank)")
    name: str = Field(..., description="Display name in Thai / English")
    vertical: str = Field(..., description="Industry vertical (beauty, e-commerce, banking, healthcare)")
    aliases: List[str] = Field(default_factory=list, description="Common spelling variations / slang in Thai")
    official_domains: List[str] = Field(default_factory=list, description="Official website domains for citation matching")
    is_focal_brand: bool = Field(default=False, description="True if this is our primary brand being audited")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class VerticalConfig(BaseModel):
    vertical_id: str
    name_th: str
    name_en: str
    focal_brands: List[str]
    competitor_brands: List[str]
    categories: List[str]
    channels: List[str] = Field(default_factory=lambda: ["google_search", "tiktok", "shopee", "lazada", "pantip", "ai_chat"])
