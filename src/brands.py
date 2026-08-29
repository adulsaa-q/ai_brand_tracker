# src/brands.py
"""Canonical brand identity resolution.

Phase 0 remediation: OpportunityFinder compared the vertical's ``focal_brand``
(an id like ``"shopee"``) directly against ``brand_mentions[].brand_name``
(a display name like ``"Shopee Thailand"``). They never matched, so the focal
brand was treated as absent from every query and the strategy memo was wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrandIdentity:
    brand_id: str
    name: str
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def identifiers(self) -> set[str]:
        """All lowercased strings that legitimately refer to this brand."""
        out = {self.brand_id.lower(), self.name.lower()}
        out.update(a.lower() for a in self.aliases)
        return {s for s in out if s}

    def matches(self, candidate: str) -> bool:
        return bool(candidate) and candidate.strip().lower() in self.identifiers


def resolve_focal_brand(vertical_cfg: dict) -> BrandIdentity:
    """Resolve the vertical's focal brand to a canonical identity.

    Resolution order: explicit ``is_focal_brand`` flag on a brand entry, then a
    match of the vertical-level ``focal_brand`` value against any brand's
    id / name / alias, then the first brand as a last resort.
    """
    brands = vertical_cfg.get("brands", []) or []
    focal_hint = str(vertical_cfg.get("focal_brand", "")).strip().lower()

    def _identity(b: dict) -> BrandIdentity:
        return BrandIdentity(
            brand_id=b.get("id", b.get("name", "focal")),
            name=b.get("name", b.get("id", "focal")),
            aliases=tuple(b.get("aliases", []) or []),
        )

    for b in brands:
        if b.get("is_focal_brand"):
            return _identity(b)

    if focal_hint:
        for b in brands:
            ident = _identity(b)
            if focal_hint in ident.identifiers:
                return ident

    if brands:
        return _identity(brands[0])
    return BrandIdentity(brand_id="focal", name=vertical_cfg.get("focal_brand", "focal") or "focal")
