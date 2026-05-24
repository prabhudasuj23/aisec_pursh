from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ──────────────────────────────────────────────────────────
    environment: Literal["local", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Supabase (OIDC IdP) ──────────────────────────────────────────────────
    # e.g. https://xyzabcdef.supabase.co
    supabase_url: str = ""
    # Public anon key — not a secret, but kept in env for flexibility
    supabase_anon_key: str = ""
    # Used as fallback HS256 secret if RS256 JWKS is unavailable
    supabase_jwt_secret: str = ""

    # ── AWS ───────────────────────────────────────────────────────────────────
    aws_region: str = "us-east-1"

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "aisec"
    api_v1_prefix: str = "/api/v1"
    # Comma-separated list of allowed CORS origins
    cors_origins: str = "http://localhost:3000"

    # ── Database ──────────────────────────────────────────────────────────────
    # asyncpg DSN: postgresql+asyncpg://user:pass@host/db
    database_url: str = "postgresql+asyncpg://aisec:aisec@localhost:5432/aisec"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
