import httpx
import pytest

from mcp_ai_agent_lab.main import create_app


@pytest.mark.asyncio
async def test_status_fixture_is_degraded() -> None:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/services/order-api/status")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_metrics_fixture_has_required_measurements() -> None:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/services/order-api/metrics")

    assert response.status_code == 200
    assert set(response.json()) >= {"latency_ms", "error_rate", "request_count"}


@pytest.mark.asyncio
async def test_logs_support_limit_validation() -> None:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        valid = await client.get("/services/order-api/logs?limit=1")
        invalid = await client.get("/services/order-api/logs?limit=0")

    assert len(valid.json()["entries"]) == 1
    assert invalid.status_code == 422


@pytest.mark.asyncio
async def test_unknown_service_returns_404() -> None:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/services/unknown-api/status")

    assert response.status_code == 404
