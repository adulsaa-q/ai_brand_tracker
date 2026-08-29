from abc import ABC, abstractmethod

from src.models.observations import RawObservation


class BaseObservationEngine(ABC):
    def __init__(self, model_name: str, api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def observe(
        self,
        query_id: str,
        query_text: str,
        target_brands: list[str],
        brand_aliases: dict[str, list[str]] | None = None,
    ) -> RawObservation:
        """Observe one query.

        ``target_brands`` are canonical display names (used in prompts / output).
        ``brand_aliases`` maps a canonical name to alt spellings (Thai, slang,
        short forms). Substring-matching engines (serper, tavily) must match
        against name + aliases; LLM engines only need the names.
        """


def match_terms(brand: str, brand_aliases: dict[str, list[str]] | None) -> list[str]:
    """Lowercased strings that count as a mention of ``brand``."""
    terms = {brand.lower()}
    for alias in (brand_aliases or {}).get(brand, []):
        if alias and len(alias) >= 2:
            terms.add(alias.lower())
    return [t for t in terms if t]
