from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class PurshSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="PURSH_",
    )

    environment: Literal["local", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Supabase (Auth + DB) ─────────────────────────────────────────────────
    supabase_url: str = "https://REPLACE_WITH_SUPABASE_PROJECT_REF.supabase.co"
    supabase_anon_key: str = "REPLACE_WITH_SUPABASE_ANON_KEY"
    supabase_service_role_key: str = "REPLACE_WITH_SUPABASE_SERVICE_ROLE_KEY"
    database_url: str = "postgresql+asyncpg://postgres:REPLACE@db.REPLACE.supabase.co:5432/postgres"

    # ── AWS ──────────────────────────────────────────────────────────────────
    aws_region: str = "us-east-1"
    s3_bucket_lab_results: str = "pursh-lab-results-REPLACE_ENV"

    # ── App ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3001"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> PurshSettings:
    return PurshSettings()
