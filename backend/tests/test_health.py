import pytest
import httpx


@pytest.mark.asyncio
async def test_health_liveness(async_client: httpx.AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "Federated Agentic Mesh" in data["service"]


@pytest.mark.asyncio
async def test_health_readiness(async_client: httpx.AsyncClient):
    resp = await async_client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert "dependencies" in data
    assert data["dependencies"]["database"]["status"] == "connected"
    assert "ollama_local_runtime" in data["dependencies"]
