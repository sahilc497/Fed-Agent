import pytest
import httpx


@pytest.mark.asyncio
async def test_employee_cannot_create_user(async_client: httpx.AsyncClient, sales_rep_headers: dict):
    payload = {
        "email": "hacked@mesh.internal",
        "password": "Password123!",
        "full_name": "Hacker",
        "department_id": 1,
        "role": "admin"
    }
    resp = await async_client.post("/api/v1/users", json=payload, headers=sales_rep_headers)
    assert resp.status_code == 403
    assert "administrator" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sales_employee_cannot_access_audit_logs(async_client: httpx.AsyncClient, sales_rep_headers: dict):
    resp = await async_client.get("/api/v1/audit", headers=sales_rep_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_auditor_can_access_audit_logs(async_client: httpx.AsyncClient, auditor_headers: dict):
    resp = await async_client.get("/api/v1/audit", headers=auditor_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_department_summary_is_scoped(
    async_client: httpx.AsyncClient,
    sales_rep_headers: dict,
    hr_specialist_headers: dict
):
    # Sales rep gets Sales summary
    sales_resp = await async_client.get("/api/v1/departments/me/summary", headers=sales_rep_headers)
    assert sales_resp.status_code == 200
    assert sales_resp.json()["department_code"] == "sales"

    # HR specialist gets HR summary
    hr_resp = await async_client.get("/api/v1/departments/me/summary", headers=hr_specialist_headers)
    assert hr_resp.status_code == 200
    assert hr_resp.json()["department_code"] == "hr"
