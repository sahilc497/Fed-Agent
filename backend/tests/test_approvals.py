import uuid
import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.approval_service import ApprovalService
from app.repositories.user_repo import UserRepository
from app.schemas.approval import ApprovalCreate


async def create_fresh_pending_approval(db: AsyncSession, requester_email: str = "finance.analyst@mesh.enterprise.internal") -> str:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(requester_email)
    app_svc = ApprovalService(db)
    data = ApprovalCreate(
        action_type="payment_execution",
        target_resource="finance_invoice:TEST-PAYMENT",
        requested_operation="execute_wire_transfer",
        payload={"amount": 10000.0, "vendor": "Test Vendor Corp"},
        idempotency_key=str(uuid.uuid4())
    )
    req = await app_svc.create_approval_request(user, data)
    return req.id


@pytest.mark.asyncio
async def test_pending_action_cannot_execute(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    finance_manager_headers: dict
):
    approval_id = await create_fresh_pending_approval(db_session)
    resp = await async_client.post(f"/api/v1/approvals/{approval_id}/execute", headers=finance_manager_headers)
    assert resp.status_code == 403
    assert "must be 'approved'" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_self_approval_prevented(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    finance_analyst_headers: dict
):
    # Requester creates fresh approval and attempts self-approval
    approval_id = await create_fresh_pending_approval(db_session, "finance.analyst@mesh.enterprise.internal")
    payload = {"decision": "approve", "reason": "Self approving my transfer"}
    resp = await async_client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json=payload,
        headers=finance_analyst_headers
    )
    # Blocked by role and self-approval prevention
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_authorized_manager_approval_and_execution(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    finance_manager_headers: dict
):
    # Create fresh pending approval
    approval_id = await create_fresh_pending_approval(db_session)

    # 1. Finance manager approves the pending request
    payload = {"decision": "approve", "reason": "Verified invoice against vendor contract"}
    appr_resp = await async_client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json=payload,
        headers=finance_manager_headers
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"

    # 2. Execute approved action
    exec_resp = await async_client.post(
        f"/api/v1/approvals/{approval_id}/execute",
        headers=finance_manager_headers
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["execution_status"] == "success"

    # 3. Duplicate execution MUST be prevented
    dup_resp = await async_client.post(
        f"/api/v1/approvals/{approval_id}/execute",
        headers=finance_manager_headers
    )
    assert dup_resp.status_code == 403
    assert "already been executed" in dup_resp.json()["detail"].lower()
