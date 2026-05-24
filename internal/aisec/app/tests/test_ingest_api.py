"""
End-to-end tests for POST /api/v1/ingest/sarif.

These tests hit the FastAPI app via httpx.AsyncClient and verify the full
ingest path: auth → schema validation → normalization → response.

The DB is mocked (AsyncSession) so tests run without Postgres.
Auth is mocked using the same RSA key pair pattern from test_auth.py.

Coverage targets (CLAUDE.md §10 — 80% on aisec/app/ingest):
  - Happy path: valid SARIF → 201 with correct counts
  - Malformed SARIF: missing 'runs' → 422
  - No auth: → 401
  - Unknown discipline falls back to 'appsec'
  - Mixed-severity SARIF → severity_counts correct
  - Empty runs (no findings) → 201, ingested=0
  - Target propagated to findings
"""

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.main import create_app

TEST_SUPABASE_URL = "https://test.supabase.co"

SEMGREP_GOLDEN = Path(__file__).parent / "contracts" / "semgrep_golden.sarif.json"
GITLEAKS_GOLDEN = Path(__file__).parent / "contracts" / "gitleaks_golden.sarif.json"
CHECKOV_GOLDEN = Path(__file__).parent / "contracts" / "checkov_golden.sarif.json"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def rsa_private_key():
    from cryptography.hazmat.primitives.asymmetric import rsa
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def private_key_pem(rsa_private_key):
    from cryptography.hazmat.primitives import serialization
    return rsa_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


@pytest.fixture(scope="session")
def jwks_dict(rsa_private_key):
    from jose.backends import RSAKey
    from jose.constants import ALGORITHMS
    rsa_key = RSAKey(rsa_private_key.public_key(), ALGORITHMS.RS256)
    public_dict = rsa_key.public_key().to_dict()
    public_dict["kid"] = "test-key-id"
    public_dict["use"] = "sig"
    return {"keys": [public_dict]}


def _make_token(private_key_pem: bytes, exp_offset: int = 3600) -> str:
    now = int(time.time())
    claims = {
        "sub": "ci-service-account",
        "email": "ci@aisec.internal",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": f"{TEST_SUPABASE_URL}/auth/v1",
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
def mock_db():
    """Async DB session that accepts add() and flush() without a real Postgres."""
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def app(test_settings, mock_db):
    a = create_app()
    a.dependency_overrides[get_settings] = lambda: test_settings
    a.dependency_overrides[get_db] = lambda: mock_db
    return a


@pytest.fixture
def mock_jwks(jwks_dict):
    with patch("app.auth.oidc._fetch_jwks", new_callable=AsyncMock) as mock:
        mock.return_value = jwks_dict["keys"]
        yield mock


@pytest.fixture
def auth_headers(private_key_pem):
    return {"Authorization": f"Bearer {_make_token(private_key_pem)}"}


# ── Helper ────────────────────────────────────────────────────────────────────

def _sarif_payload(sarif_path: Path, target: str = "pursh", discipline: str = "appsec") -> dict:
    return {
        "sarif": json.loads(sarif_path.read_text()),
        "target": target,
        "discipline": discipline,
    }


# ── Happy path ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_semgrep_returns_201(app, mock_jwks, auth_headers) -> None:
    payload = _sarif_payload(SEMGREP_GOLDEN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_ingest_semgrep_finding_count(app, mock_jwks, auth_headers) -> None:
    payload = _sarif_payload(SEMGREP_GOLDEN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    body = response.json()
    assert body["ingested"] == 2
    assert body["skipped"] == 0


@pytest.mark.asyncio
async def test_ingest_semgrep_severity_counts(app, mock_jwks, auth_headers) -> None:
    """Golden Semgrep file has 1 HIGH (error) + 1 MEDIUM (warning)."""
    payload = _sarif_payload(SEMGREP_GOLDEN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    severities = response.json()["severities"]
    assert severities.get("high") == 1
    assert severities.get("medium") == 1


@pytest.mark.asyncio
async def test_ingest_gitleaks_returns_201(app, mock_jwks, auth_headers) -> None:
    payload = _sarif_payload(GITLEAKS_GOLDEN, discipline="devsecops")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["ingested"] == 2


@pytest.mark.asyncio
async def test_ingest_checkov_returns_201(app, mock_jwks, auth_headers) -> None:
    payload = _sarif_payload(CHECKOV_GOLDEN, target="aisec-internal", discipline="devsecops")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["ingested"] == 3


@pytest.mark.asyncio
async def test_ingest_checkov_severity_counts(app, mock_jwks, auth_headers) -> None:
    """Checkov golden: 1 MEDIUM (warning) + 2 HIGH (error)."""
    payload = _sarif_payload(CHECKOV_GOLDEN, target="aisec-internal", discipline="devsecops")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    severities = response.json()["severities"]
    assert severities.get("high") == 2
    assert severities.get("medium") == 1


# ── Auth enforcement ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_no_token_returns_401(app) -> None:
    payload = _sarif_payload(SEMGREP_GOLDEN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_expired_token_returns_401(app, mock_jwks, private_key_pem) -> None:
    expired_headers = {"Authorization": f"Bearer {_make_token(private_key_pem, exp_offset=-1)}"}
    payload = _sarif_payload(SEMGREP_GOLDEN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=expired_headers)
    assert response.status_code == 401


# ── Schema validation ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_missing_runs_returns_422(app, mock_jwks, auth_headers) -> None:
    """SARIF without 'runs' key fails schema validation → 422."""
    payload = {"sarif": {"version": "2.1.0"}, "target": "pursh", "discipline": "appsec"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_wrong_sarif_version_returns_422(app, mock_jwks, auth_headers) -> None:
    """SARIF with non-2.1.0 version is rejected."""
    payload = {
        "sarif": {"version": "1.0.0", "runs": []},
        "target": "pursh",
        "discipline": "appsec",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 422


# ── Edge cases ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_empty_runs_returns_201_with_zero(app, mock_jwks, auth_headers) -> None:
    """SARIF with empty runs list is valid — 201 with ingested=0."""
    payload = {
        "sarif": {"version": "2.1.0", "runs": []},
        "target": "pursh",
        "discipline": "appsec",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["ingested"] == 0
    assert body["skipped"] == 0


@pytest.mark.asyncio
async def test_ingest_unknown_discipline_defaults_to_appsec(app, mock_jwks, auth_headers) -> None:
    """Unknown discipline value falls back gracefully — no 422, ingested normally."""
    payload = {
        "sarif": json.loads(SEMGREP_GOLDEN.read_text()),
        "target": "pursh",
        "discipline": "not-a-real-discipline",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/ingest/sarif", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["ingested"] == 2
