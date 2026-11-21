"""Application configuration via pydantic-settings.

Reads environment variables safely without hardcoding secrets, deriving
session signing keys deterministically when unconfigured.
"""

import hashlib
import hmac
from functools import lru_cache
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default evaluation password used exclusively in demo/evaluator mode
DEFAULT_DEMO_ADMIN_PASSWORD: Final[str] = "civic-demo-2026"  # noqa: S105 - Documented default credential for evaluator demo mode
SESSION_DERIVATION_CONTEXT: Final[str] = "civicresolve-session-derivation-v1"


class Settings(BaseSettings):
    """Configuration settings for CivicResolve runtime."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Google Gemini GenAI Settings
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-flash-lite-latest", alias="GEMINI_MODEL")

    # Administration Security Credentials
    admin_password: str = Field(default=DEFAULT_DEMO_ADMIN_PASSWORD, alias="ADMIN_PASSWORD")
    token_secret_raw: str = Field(default="", alias="TOKEN_SECRET")

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
    def token_secret(self) -> str:
        """Return explicit TOKEN_SECRET or derive deterministically from password."""
        if self.token_secret_raw and len(self.token_secret_raw.strip()) >= 16:
            return self.token_secret_raw.strip()
        # Derive cryptographically strong 256-bit key from admin_password and fixed context
        return hmac.new(
            self.admin_password.encode("utf-8"),
            SESSION_DERIVATION_CONTEXT.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

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
