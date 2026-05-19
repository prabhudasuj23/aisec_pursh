"""
Pursh Supabase Auth integration.

Pursh uses Supabase Auth directly (separate from AISec's OIDC federation).
Supabase Auth handles email+password sign-up, email verification, and MFA.

Two roles are enforced by RLS policies in Supabase:
- patient: can read/write only their own records
- doctor: can read assigned patients' records

Why Supabase RLS for Pursh?
RLS (Row-Level Security) is PostgreSQL's native access control mechanism.
It enforces authorization at the database layer — even if application code
has a bug that passes the wrong user_id, Postgres blocks cross-user access.
This maps to HIPAA §164.312(a)(1) (access control) and demonstrates
defense-in-depth for the ASVS V2.1.1 requirement.
"""

import time
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from pursh.backend.core.config import PurshSettings, get_settings
from pursh.backend.core.logging import get_logger, hash_patient_id

logger = get_logger(__name__)
_bearer = HTTPBearer(auto_error=False)

_jwks_cache: dict[str, Any] = {}
_JWKS_TTL = 300


class PurshUser(BaseModel):
    sub: str         # Supabase user UUID
    email: str
    role: str        # "patient" or "doctor"
    # Hashed version safe for logging (never log raw sub)

    @property
    def log_id(self) -> str:
        return hash_patient_id(self.sub)


async def _fetch_jwks(settings: PurshSettings) -> list[dict[str, Any]]:
    now = time.monotonic()
    if _jwks_cache and (now - _jwks_cache.get("cached_at", 0)) < _JWKS_TTL:
        return _jwks_cache["keys"]  # type: ignore[return-value]
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            keys = resp.json().get("keys", [])
            _jwks_cache["keys"] = keys
            _jwks_cache["cached_at"] = now
            return keys
    except Exception as exc:
        if _jwks_cache:
            return _jwks_cache["keys"]  # type: ignore[return-value]
        raise HTTPException(status_code=503, detail="Auth service unavailable.") from exc


async def require_pursh_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: PurshSettings = Depends(get_settings),
) -> PurshUser:
    unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauth
    token = credentials.credentials
    try:
        jwks = await _fetch_jwks(settings)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        rsa_key = next((k for k in jwks if k.get("kid") == kid), jwks[0] if jwks else None)
        if not rsa_key:
            raise unauth
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
        )
        sub = payload.get("sub", "")
        email = payload.get("email", "")
        # Supabase stores app_metadata.role for custom roles
        role = payload.get("app_metadata", {}).get("role", "patient")
        if not sub or not email:
            raise unauth
        logger.info("pursh_auth_success", log_id=hash_patient_id(sub), role=role)
        return PurshUser(sub=sub, email=email, role=role)
    except HTTPException:
        raise
    except JWTError as exc:
        logger.warning("pursh_jwt_failed", error=str(exc))
        raise unauth from exc


async def require_doctor(user: PurshUser = Depends(require_pursh_user)) -> PurshUser:
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctor role required.")
    return user
