"""Application configuration via pydantic-settings.

Reads environment variables safely without hardcoding secrets.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for CivicResolve runtime."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Google Gemini GenAI Settings
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # Administration Security Credentials
    admin_password: str = Field(default="civic-demo-2026", alias="ADMIN_PASSWORD")
    token_secret: str = Field(
        default="civicresolve-secret-key-change-in-production-min-32-chars",
        alias="TOKEN_SECRET",
    )

    # Location Customization
    city_name: str = Field(default="Coimbatore", alias="CITY_NAME")

    # Storage (Upstash Redis)
    upstash_redis_rest_url: str = Field(default="", alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str = Field(default="", alias="UPSTASH_REDIS_REST_TOKEN")

    # Deployment Environment
    vercel_env: str = Field(default="development", alias="VERCEL_ENV")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")

    @property
    def is_production(self) -> bool:
        """Return True if executing in live production environment."""
        return self.vercel_env.lower() == "production"

    @property
    def is_in_memory_storage(self) -> bool:
        """Return True if using the in-memory repository store."""
        return not bool(self.upstash_redis_rest_url and self.upstash_redis_rest_token)

    @property
    def has_gemini_key(self) -> bool:
        """Return True if a Gemini API key is configured."""
        return bool(self.gemini_api_key and len(self.gemini_api_key.strip()) > 5)


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
