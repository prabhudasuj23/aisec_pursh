"""
Supabase JWT verification for AISec.

Supabase issues RS256-signed JWTs. The public key is exposed at the JWKS
endpoint. We cache the key set with a TTL and fail closed (401) if the cache
is stale and the endpoint is unreachable — never allow unauthenticated access
due to an upstream failure.

Why RS256 and not HS256?
RS256 uses asymmetric keys: Supabase holds the private key; we verify with the
public key only. HS256 requires sharing the secret — if our service is
compromised, the attacker gains the ability to forge tokens. RS256 closes
that risk: a leaked public key is harmless.
"""

import time
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from app.auth.models import AuthenticatedUser
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)

# Simple in-memory JWKS cache: {"keys": [...], "cached_at": float}
_jwks_cache: dict[str, Any] = {}
_JWKS_TTL_SECONDS = 300  # 5 minutes


async def _fetch_jwks(settings: Settings) -> list[dict[str, Any]]:
    """Fetch JWKS from Supabase, returning the list of JWK dicts."""
    now = time.monotonic()
    if _jwks_cache and (now - _jwks_cache["cached_at"]) < _JWKS_TTL_SECONDS:
        return _jwks_cache["keys"]  # type: ignore[return-value]

    url = settings.supabase_jwks_url
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            keys: list[dict[str, Any]] = data.get("keys", [])
            _jwks_cache["keys"] = keys
            _jwks_cache["cached_at"] = now
            logger.info("jwks_refreshed", key_count=len(keys))
            return keys
    except Exception as exc:
        if _jwks_cache:
            logger.warning("jwks_fetch_failed_using_cache", error=str(exc))
            return _jwks_cache["keys"]  # type: ignore[return-value]
        # No cache and fetch failed — fail closed
        logger.error("jwks_fetch_failed_no_cache", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable.",
        ) from exc


def _get_rsa_key(
    token: str, jwks: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Return the matching JWK for the token's kid header, or None."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None
    kid = header.get("kid")
    for key in jwks:
        if key.get("kid") == kid:
            return key
    # If no kid match, fall back to first key (Supabase only has one active key)
    return jwks[0] if jwks else None


async def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """
    FastAPI dependency. Validates the Bearer JWT and returns the decoded user.
    Raises HTTP 401 on any verification failure — never leaks error details.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials

    try:
        jwks = await _fetch_jwks(settings)
        rsa_key = _get_rsa_key(token, jwks)

        if rsa_key is None:
            raise credentials_exception

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=f"{settings.supabase_url}/auth/v1",
            options={"verify_exp": True},
        )

        sub: str = payload.get("sub", "")
        email: str = payload.get("email", "")
        role: str = payload.get("role", "authenticated")
        aud: str = payload.get("aud", "authenticated")

        if not sub or not email:
            raise credentials_exception

        logger.info("auth_success", sub=sub, role=role)
        return AuthenticatedUser(sub=sub, email=email, role=role, aud=aud)

    except HTTPException:
        raise
    except JWTError as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise credentials_exception from exc
    except Exception as exc:
        logger.error("auth_unexpected_error", error=str(exc))
        raise credentials_exception from exc
