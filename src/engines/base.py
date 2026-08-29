from abc import ABC, abstractmethod

from src.models.observations import RawObservation


class BaseObservationEngine(ABC):
    def __init__(self, model_name: str, api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        pass
