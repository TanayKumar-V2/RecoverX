from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RevLoop"
    app_env: str = "development"

    cohere_api_key: str | None = Field(default=None)
    cohere_model: str = "command-a-plus-05-2026"

    database_url: str = "sqlite:///./revloop.db"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_cohere_api_key(self) -> str:
        if not self.cohere_api_key:
            raise ValueError(
                "COHERE_API_KEY is not configured. "
                "Add it to your .env file."
            )

        return self.cohere_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()