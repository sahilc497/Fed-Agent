import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.gateway.service import FederationGatewayService
from app.gateway.schemas import FederationRequest


@pytest.mark.asyncio
async def test_gateway_permitted_sales_to_finance(db_session: AsyncSession):
    gateway = FederationGatewayService(db_session)
    dummy_user = User(id=4, email="sales.rep@mesh.enterprise.internal", role="department_employee", department_id=1)

    req = FederationRequest(
        requesting_agent="sales_agent",
        requesting_user_id=4,
        requesting_department="sales",
        target_department="finance",
        business_purpose="opportunity_finance_status",
        requested_fields=["opportunity_id", "finance_status", "status"],
        correlation_id="test-corr-gw-001"
    )

    res = await gateway.execute_federated_request(dummy_user, req)
    assert res.is_allowed
    assert res.status_code == 200
    assert len(res.denied_fields) == 0


@pytest.mark.asyncio
async def test_gateway_denies_prohibited_salary_field(db_session: AsyncSession):
    gateway = FederationGatewayService(db_session)
    dummy_user = User(id=4, email="sales.rep@mesh.enterprise.internal", role="department_employee", department_id=1)

    req = FederationRequest(
        requesting_agent="sales_agent",
        requesting_user_id=4,
        requesting_department="sales",
        target_department="finance",
        business_purpose="opportunity_finance_status",
        requested_fields=["opportunity_id", "salary"],  # Prohibited field
        correlation_id="test-corr-gw-002"
    )

    res = await gateway.execute_federated_request(dummy_user, req)
    assert not res.is_allowed
    assert res.status_code == 403
    assert "salary" in res.denied_fields


@pytest.mark.asyncio
async def test_gateway_denies_unauthorized_department_bridge(db_session: AsyncSession):
    gateway = FederationGatewayService(db_session)
    dummy_user = User(id=4, email="sales.rep@mesh.enterprise.internal", role="department_employee", department_id=1)

    # Sales to HR has no approved generic bridge
    req = FederationRequest(
        requesting_agent="sales_agent",
        requesting_user_id=4,
        requesting_department="sales",
        target_department="hr",
        business_purpose="unauthorized_crawl",
        requested_fields=["employee_records"],
        correlation_id="test-corr-gw-003"
    )

    res = await gateway.execute_federated_request(dummy_user, req)
    assert not res.is_allowed
    assert res.status_code == 403
