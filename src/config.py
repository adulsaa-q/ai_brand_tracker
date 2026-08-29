from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class Settings(BaseModel):
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    log_level: str = Field(default="INFO")
    db_path: str = Field(default="data/intelligence.db")

    openrouter_api_key: SecretStr | None = Field(default=None)
    gemini_api_key: SecretStr | None = Field(default=None)
    tavily_api_key: SecretStr | None = Field(default=None)
    serper_api_key: SecretStr | None = Field(default=None)
    openai_api_key: SecretStr | None = Field(default=None)
    anthropic_api_key: SecretStr | None = Field(default=None)
    perplexity_api_key: SecretStr | None = Field(default=None)

    default_vertical: str = Field(default="ecommerce_retail_th")
    default_seed: int = Field(default=42)

    @classmethod
    def load_from_env(cls) -> Settings:
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            db_path=os.getenv("DB_PATH", "data/intelligence.db"),
            openrouter_api_key=SecretStr(os.getenv("OPENROUTER_API_KEY")) if os.getenv("OPENROUTER_API_KEY") else None,
            gemini_api_key=SecretStr(os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None,
            tavily_api_key=SecretStr(os.getenv("TAVILY_API_KEY")) if os.getenv("TAVILY_API_KEY") else None,
            serper_api_key=SecretStr(os.getenv("SERPER_API_KEY")) if os.getenv("SERPER_API_KEY") else None,
            openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None,
            anthropic_api_key=SecretStr(os.getenv("ANTHROPIC_API_KEY")) if os.getenv("ANTHROPIC_API_KEY") else None,
            perplexity_api_key=SecretStr(os.getenv("PERPLEXITY_API_KEY")) if os.getenv("PERPLEXITY_API_KEY") else None,
        )


app_settings = Settings.load_from_env()
