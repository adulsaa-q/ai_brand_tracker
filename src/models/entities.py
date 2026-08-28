from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class BrandEntity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., description="Unique slug identifier")
    name: str = Field(..., description="Canonical display name")
    vertical: str = Field(..., description="Industry vertical category")
    aliases: List[str] = Field(default_factory=list, description="Thai slang, typos, aliases")
    official_domains: List[str] = Field(default_factory=list, description="Official domain names")
    is_focal_brand: bool = Field(default=False, description="Primary audited entity")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class VerticalConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    vertical_id: str = Field(...)
    name_th: str = Field(...)
    name_en: str = Field(...)
    focal_brand_id: str = Field(...)
    brands: List[BrandEntity] = Field(default_factory=list)
