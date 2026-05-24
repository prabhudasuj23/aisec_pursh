"""
Auth tests for the /api/v1/me endpoint.

We test the JWT verification logic without a live Supabase project by:
1. Generating a local RSA key pair
2. Mocking the JWKS endpoint to return the public key
3. Issuing our own test JWTs with the private key

This validates that:
- Valid JWT → 200
- Expired JWT → 401
- No JWT → 401
- Tampered JWT (bad signature) → 401
- Missing required claims → 401
"""

import time
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import Settings, get_settings
from app.main import create_app

TEST_SUPABASE_URL = "https://test.supabase.co"


# ── Test RSA key pair (generated once per test session) ───────────────────────

@pytest.fixture(scope="session")
def rsa_private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def rsa_public_key(rsa_private_key):
    return rsa_private_key.public_key()


@pytest.fixture(scope="session")
def jwks_dict(rsa_public_key):
    """Return a JWKS dict containing our test public key."""
    from jose.backends import RSAKey
    from jose.constants import ALGORITHMS

    rsa_key = RSAKey(rsa_public_key, ALGORITHMS.RS256)
    public_dict = rsa_key.public_key().to_dict()
    public_dict["kid"] = "test-key-id"
    public_dict["use"] = "sig"
    return {"keys": [public_dict]}


@pytest.fixture(scope="session")
def private_key_pem(rsa_private_key):
    return rsa_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


def make_token(
    private_key_pem: bytes,
    sub: str = "user-uuid-123",
    email: str = "test@example.com",
    role: str = "authenticated",
    aud: str = "authenticated",
    iss: str = f"{TEST_SUPABASE_URL}/auth/v1",
    exp_offset: int = 3600,
) -> str:
    now = int(time.time())
    claims = {
        "sub": sub,
        "email": email,
        "role": role,
        "aud": aud,
        "iss": iss,
        "iat": now,
        "exp": now + exp_offset,
    }
    return jwt.encode(claims, private_key_pem, algorithm="RS256", headers={"kid": "test-key-id"})


@pytest.fixture
def test_settings():
    return Settings(
        supabase_url=TEST_SUPABASE_URL,
        supabase_anon_key="test-anon-key",
        supabase_jwt_secret="test-jwt-secret",
        environment="local",
    )


@pytest.fixture
def app(test_settings):
    a = create_app()
    a.dependency_overrides[get_settings] = lambda: test_settings
    return a


@pytest.fixture
def mock_jwks(jwks_dict):
    """Patch the JWKS fetch to return our test key without hitting Supabase."""
    with patch("app.auth.oidc._fetch_jwks", new_callable=AsyncMock) as mock:
        mock.return_value = jwks_dict["keys"]
        yield mock


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_valid_jwt_returns_200(app, mock_jwks, private_key_pem) -> None:
    token = make_token(private_key_pem)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["sub"] == "user-uuid-123"
    assert body["email"] == "test@example.com"
    assert body["role"] == "authenticated"


@pytest.mark.asyncio
async def test_no_token_returns_401(app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_returns_401(app, mock_jwks, private_key_pem) -> None:
    token = make_token(private_key_pem, exp_offset=-1)  # already expired
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_returns_401(app, mock_jwks, private_key_pem) -> None:
    token = make_token(private_key_pem)
    # Flip one character in the signature segment
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + "." + parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {tampered}"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_missing_email_returns_401(app, mock_jwks, private_key_pem) -> None:
    """JWT with no email claim should be rejected."""
    now = int(time.time())
    claims = {
        "sub": "user-uuid-123",
        # email intentionally omitted
        "role": "authenticated",
        "aud": "authenticated",
        "iss": f"{TEST_SUPABASE_URL}/auth/v1",
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(claims, private_key_pem, algorithm="RS256", headers={"kid": "test-key-id"})
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 401
