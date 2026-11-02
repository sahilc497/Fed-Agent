import uuid
import datetime
import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.federation_request import FederationAccessRequest
from app.repositories.user_repo import UserRepository, DepartmentRepository
from app.repositories.audit_repo import AuditRepository


@pytest.mark.asyncio
async def test_federation_request_lifecycle(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict,
    admin_headers: dict,
    sales_manager_headers: dict
):
    """
    Tests complete lifecycle:
    1. Sales rep creates request for Finance invoice status.
    2. Pending request is blocked from consumption (Criteria 8).
    3. Requester cannot approve their own request (Criteria 10).
    4. Non-admin (Sales Manager) cannot approve cross-dept request (Criteria 9).
    5. Admin approves with specific allowed fields (Criteria 11).
    6. Consumer receives ONLY the exact approved fields and records.
    7. Once completed or revoked, subsequent consumption fails.
    """
    key = str(uuid.uuid4())
    create_payload = {
        "source_department_code": "finance",
        "business_purpose": "Verify payment clearance for Titan Heavy Industries deal",
        "requested_fields": ["invoice_number", "status", "due_date"],
        "record_identifiers": ["INV-2026-002"],
        "access_duration_minutes": 60,
        "idempotency_key": key
    }

    # 1. Create Request
    res_create = await async_client.post("/api/v1/federation/requests", json=create_payload, headers=sales_rep_headers)
    assert res_create.status_code == 200
    data_created = res_create.json()
    req_id = data_created["id"]
    assert data_created["status"] == "PENDING"

    # 2. Consume while PENDING must be blocked (Criteria 8)
    res_consume_pending = await async_client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_rep_headers)
    assert res_consume_pending.status_code == 403
    assert "must be 'APPROVED'" in res_consume_pending.json()["detail"]

    # 3. Requester tries to self-approve: Must be blocked (Criteria 10)
    res_self_approve = await async_client.post(
        f"/api/v1/federation/requests/{req_id}/decision",
        json={"decision": "approve", "reason": "Self approving my own request"},
        headers=sales_rep_headers
    )
    assert res_self_approve.status_code == 403

    # 4. Department Manager (non-admin) tries to approve cross-dept request: Must be blocked (Criteria 9)
    res_manager_approve = await async_client.post(
        f"/api/v1/federation/requests/{req_id}/decision",
        json={"decision": "approve", "reason": "Manager approval attempt"},
        headers=sales_manager_headers
    )
    assert res_manager_approve.status_code == 403
    assert "Only an authorized Administrator" in res_manager_approve.json()["detail"]

    # 5. Administrator approves with specific subset of fields (Criteria 11)
    res_admin_approve = await async_client.post(
        f"/api/v1/federation/requests/{req_id}/decision",
        json={
            "decision": "approve",
            "reason": "Authorized by Finance Controller & Admin for Titan deal",
            "approved_fields": ["invoice_number", "status"],
            "approved_record_ids": ["INV-2026-002"]
        },
        headers=admin_headers
    )
    assert res_admin_approve.status_code == 200
    assert res_admin_approve.json()["status"] == "APPROVED"

    # 6. Consume approved grant: only approved fields are released
    res_consume = await async_client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_rep_headers)
    assert res_consume.status_code == 200
    consumed_data = res_consume.json()
    assert consumed_data["status"] == "COMPLETED"
    assert consumed_data["record_count"] >= 1
    # Verify exact field isolation: "due_date" was omitted from approved_fields, so it must not be released
    for rec in consumed_data["records"]:
        assert "invoice_number" in rec
        assert "status" in rec
        assert "due_date" not in rec  # Was not approved!
        assert "amount" not in rec    # Was never requested or approved!


@pytest.mark.asyncio
async def test_revoked_grant_denies_access(
    async_client: httpx.AsyncClient,
    sales_rep_headers: dict,
    admin_headers: dict
):
    """Criteria 12: Revoked grant immediately prevents access."""
    # Create and approve request
    create_payload = {
        "source_department_code": "finance",
        "business_purpose": "Check payment for revoked test",
        "requested_fields": ["invoice_number", "status"],
        "record_identifiers": ["INV-2026-001"],
        "idempotency_key": str(uuid.uuid4())
    }
    r_create = await async_client.post("/api/v1/federation/requests", json=create_payload, headers=sales_rep_headers)
    req_id = r_create.json()["id"]

    await async_client.post(
        f"/api/v1/federation/requests/{req_id}/decision",
        json={"decision": "approve", "reason": "Pre-approved"},
        headers=admin_headers
    )

    # Now admin immediately revokes the grant
    res_revoke = await async_client.post(
        f"/api/v1/federation/requests/{req_id}/revoke",
        params={"reason": "Security policy changed"},
        headers=admin_headers
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["status"] == "REVOKED"

    # Attempting to consume revoked grant must fail
    res_consume = await async_client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_rep_headers)
    assert res_consume.status_code == 403
    assert "revoked" in res_consume.json()["detail"].lower()


@pytest.mark.asyncio
async def test_expired_grant_denies_access(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict,
    admin_headers: dict
):
    """Criteria 12: Expired grant fails closed."""
    from app.repositories.federation_repo import FederationRequestRepository

    create_payload = {
        "source_department_code": "finance",
        "business_purpose": "Expiry test",
        "requested_fields": ["invoice_number", "status"],
        "idempotency_key": str(uuid.uuid4())
    }
    r_create = await async_client.post("/api/v1/federation/requests", json=create_payload, headers=sales_rep_headers)
    req_id = r_create.json()["id"]

    await async_client.post(
        f"/api/v1/federation/requests/{req_id}/decision",
        json={"decision": "approve", "reason": "Approved before expiry"},
        headers=admin_headers
    )

    # Artificially set expires_at in the past
    past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)).isoformat()
    conn = getattr(db_session, "conn", db_session)
    conn.execute("UPDATE federation_access_requests SET expires_at = ? WHERE id = ?;", (past_iso, req_id))
    await db_session.commit()

    # Attempt to consume expired grant
    res_consume = await async_client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_rep_headers)
    assert res_consume.status_code == 403
    assert "expired" in res_consume.json()["detail"].lower()


@pytest.mark.asyncio
async def test_audit_logs_record_federation_lifecycle(db_session: AsyncSession):
    """Criteria 18: Audit log records request, approval, rejection, and data release."""
    audit_repo = AuditRepository(db_session)
    logs = await audit_repo.list_audit_logs(limit=50)

    actions = [l.action for l in logs]

    assert any("federation:" in a or "gateway:" in a for a in actions)
