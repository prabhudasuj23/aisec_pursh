import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_healthz_returns_200(app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aisec"


@pytest.mark.asyncio
async def test_healthz_does_not_require_auth(app) -> None:
    """Liveness probe must be reachable without any Authorization header."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/healthz")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_correlation_id_header_returned(app) -> None:
    """Middleware must echo or generate X-Request-ID on every response."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/healthz", headers={"X-Request-ID": "test-id-123"})

    assert response.headers.get("x-request-id") == "test-id-123"


@pytest.mark.asyncio
async def test_correlation_id_generated_if_absent(app) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/healthz")

    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 36  # UUID format
