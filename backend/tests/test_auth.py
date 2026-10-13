import pytest
import httpx


@pytest.mark.asyncio
async def test_login_success(async_client: httpx.AsyncClient):
    payload = {
        "email": "admin@mesh.enterprise.internal",
        "password": "MeshSecure2026!"
    }
    resp = await async_client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@mesh.enterprise.internal"
    # Security check: Password hashes MUST NOT be exposed
    assert "hashed_password" not in data["user"]
    assert "password" not in data["user"]


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: httpx.AsyncClient):
    payload = {
        "email": "admin@mesh.enterprise.internal",
        "password": "WrongPassword123!"
    }
    resp = await async_client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_me_endpoint_with_valid_token(async_client: httpx.AsyncClient, sales_rep_headers: dict):
    resp = await async_client.get("/api/v1/auth/me", headers=sales_rep_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "sales.rep@mesh.enterprise.internal"
    assert data["role"] == "department_employee"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_invalid_token_rejected(async_client: httpx.AsyncClient):
    headers = {"Authorization": "Bearer invalid.fake.token"}
    resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 401
