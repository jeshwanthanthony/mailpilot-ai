from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MailPilot API"
    environment: str = "development"
    base_url: str = "http://127.0.0.1:8000"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    session_secret: str = "local-development-secret-change-me"
    token_encryption_key: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    supabase_url: str | None = None
    supabase_service_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def secure_cookies(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def gmail_ready(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret
            and self.supabase_url
            and self.supabase_service_key
            and self.token_encryption_key
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
