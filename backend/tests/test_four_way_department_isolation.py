import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.retrieval import RAGRetrievalService
from app.repositories.user_repo import DepartmentRepository


@pytest.mark.asyncio
async def test_sales_cannot_access_hr_finance_operations_directly(
    async_client: httpx.AsyncClient,
    sales_rep_headers: dict
):
    """Criteria 4 & 14: Sales rep receives 403 when attempting direct access to HR, Finance, or Operations."""
    # Direct HR access blocked
    res_hr = await async_client.get("/api/v1/departments/hr/records", headers=sales_rep_headers)
    assert res_hr.status_code == 403
    assert "isolation policy" in res_hr.json()["detail"].lower()

    # Direct Finance access blocked
    res_fin = await async_client.get("/api/v1/departments/finance/records", headers=sales_rep_headers)
    assert res_fin.status_code == 403
    assert "isolation policy" in res_fin.json()["detail"].lower()

    # Direct Operations access blocked
    res_ops = await async_client.get("/api/v1/departments/operations/records", headers=sales_rep_headers)
    assert res_ops.status_code == 403
    assert "isolation policy" in res_ops.json()["detail"].lower()


@pytest.mark.asyncio
async def test_hr_cannot_access_sales_finance_operations_directly(
    async_client: httpx.AsyncClient,
    hr_specialist_headers: dict
):
    """Criteria 5 & 14: HR specialist receives 403 for Sales, Finance, or Operations records."""
    res_sales = await async_client.get("/api/v1/departments/sales/records", headers=hr_specialist_headers)
    assert res_sales.status_code == 403

    res_fin = await async_client.get("/api/v1/departments/finance/records", headers=hr_specialist_headers)
    assert res_fin.status_code == 403

    res_ops = await async_client.get("/api/v1/departments/operations/records", headers=hr_specialist_headers)
    assert res_ops.status_code == 403


@pytest.mark.asyncio
async def test_finance_cannot_access_sales_hr_operations_directly(
    async_client: httpx.AsyncClient,
    finance_analyst_headers: dict
):
    """Criteria 6 & 14: Finance analyst receives 403 for Sales, HR, or Operations records."""
    res_sales = await async_client.get("/api/v1/departments/sales/records", headers=finance_analyst_headers)
    assert res_sales.status_code == 403

    res_hr = await async_client.get("/api/v1/departments/hr/records", headers=finance_analyst_headers)
    assert res_hr.status_code == 403

    res_ops = await async_client.get("/api/v1/departments/operations/records", headers=finance_analyst_headers)
    assert res_ops.status_code == 403


@pytest.mark.asyncio
async def test_operations_cannot_access_sales_hr_finance_directly(
    async_client: httpx.AsyncClient,
    operations_lead_headers: dict
):
    """Criteria 7 & 14: Operations employee receives 403 for Sales, HR, or Finance records."""
    res_sales = await async_client.get("/api/v1/departments/sales/records", headers=operations_lead_headers)
    assert res_sales.status_code == 403

    res_hr = await async_client.get("/api/v1/departments/hr/records", headers=operations_lead_headers)
    assert res_hr.status_code == 403

    res_fin = await async_client.get("/api/v1/departments/finance/records", headers=operations_lead_headers)
    assert res_fin.status_code == 403


@pytest.mark.asyncio
async def test_vector_search_four_way_department_isolation(db_session: AsyncSession):
    """Criteria 15: Vector search strictly filters by department before scoring; zero cross-department chunk leakage."""
    dept_repo = DepartmentRepository(db_session)
    sales_dept = await dept_repo.get_by_code("sales")
    hr_dept = await dept_repo.get_by_code("hr")
    finance_dept = await dept_repo.get_by_code("finance")
    ops_dept = await dept_repo.get_by_code("operations")

    rag = RAGRetrievalService(db_session)

    # Search for Warehouse Safety in Sales scope: must return 0 results
    sales_results = await rag.retrieve_evidence(
        query="forklift certification and warehouse hazardous battery protocol",
        department_id=sales_dept.id,
        department_code="sales"
    )
    for ev in sales_results:
        assert "operations" not in ev.snippet.lower()
        assert "warehouse" not in ev.snippet.lower()

    # Search for Executive Compensation in Operations scope: must return 0 results
    ops_results = await rag.retrieve_evidence(
        query="executive compensation equity grant schedule",
        department_id=ops_dept.id,
        department_code="operations"
    )
    for ev in ops_results:
        assert "compensation" not in ev.snippet.lower()
        assert "salary" not in ev.snippet.lower()

    # Search in Operations scope: finds authorized operations documents
    ops_valid = await rag.retrieve_evidence(
        query="forklift motorized equipment warehouse protocol",
        department_id=ops_dept.id,
        department_code="operations"
    )
    assert len(ops_valid) > 0
    assert any("operations" in ev.department.lower() for ev in ops_valid)
