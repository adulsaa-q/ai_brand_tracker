class MarketIntelligenceError(Exception):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EngineError(MarketIntelligenceError):
    pass


class RateLimitExceededError(EngineError):
    pass


class StructuredOutputParsingError(EngineError):
    pass


class StorageError(MarketIntelligenceError):
    pass


class EntityNotFoundError(MarketIntelligenceError):
    pass


class SchemaValidationError(MarketIntelligenceError):
    pass
