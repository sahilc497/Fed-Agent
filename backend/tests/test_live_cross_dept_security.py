import pytest
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.document import Document
from app.db.models.audit import AuditLog


@pytest.mark.asyncio
async def test_cross_dept_document_direct_id_isolation(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict,
    hr_specialist_headers: dict,
    admin_headers: dict
):
    """
    Test direct ID isolation:
    Sales employee cannot retrieve HR document by direct ID.
    HR specialist cannot retrieve Sales document by direct ID.
    Admin can retrieve documents across departments.
    """
    # 1. Locate an HR document and a Sales document from database
    hr_doc = (await db_session.execute(select(Document).where(Document.department_id == 2))).scalars().first()
    sales_doc = (await db_session.execute(select(Document).where(Document.department_id == 1))).scalars().first()

    assert hr_doc is not None, "HR document must exist in database"
    assert sales_doc is not None, "Sales document must exist in database"

    # 2. Sales rep attempts to fetch HR document by ID -> must fail with 404/Access Denied
    resp1 = await async_client.get(f"/api/v1/documents/{hr_doc.id}", headers=sales_rep_headers)
    assert resp1.status_code == 404
    assert "access denied" in resp1.json()["detail"].lower() or "not found" in resp1.json()["detail"].lower()

    # 3. HR specialist attempts to fetch Sales document by ID -> must fail with 404/Access Denied
    resp2 = await async_client.get(f"/api/v1/documents/{sales_doc.id}", headers=hr_specialist_headers)
    assert resp2.status_code == 404
    assert "access denied" in resp2.json()["detail"].lower() or "not found" in resp2.json()["detail"].lower()

    # 4. Admin can fetch both documents
    admin_resp1 = await async_client.get(f"/api/v1/documents/{hr_doc.id}", headers=admin_headers)
    assert admin_resp1.status_code == 200
    assert admin_resp1.json()["id"] == hr_doc.id

    admin_resp2 = await async_client.get(f"/api/v1/documents/{sales_doc.id}", headers=admin_headers)
    assert admin_resp2.status_code == 200
    assert admin_resp2.json()["id"] == sales_doc.id


@pytest.mark.asyncio
async def test_cross_dept_chat_unauthorized_bridges_denied_and_audited(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict,
    hr_specialist_headers: dict
):
    """
    Verify chat cross-department access without an approved federation bridge:
    - HR asking about Sales deals is strictly denied by the Orchestrator.
    - Sales asking about HR salaries/records is strictly denied by the Orchestrator.
    - Both denials persist actual 'deny' audit records in the database.
    """
    # 1. HR user asks about Sales deals
    hr_payload = {"message": "Show me all sales opportunities and pipeline deals for Apex Corp"}
    hr_chat_resp = await async_client.post("/api/v1/chat", json=hr_payload, headers=hr_specialist_headers)
    assert hr_chat_resp.status_code == 200
    hr_data = hr_chat_resp.json()
    assert "access denied" in hr_data["answer"].lower()
    assert hr_data["error"] is not None

    # 2. Sales user asks about HR salaries
    sales_payload = {"message": "List employee salaries, wages, and payroll records for engineering"}
    sales_chat_resp = await async_client.post("/api/v1/chat", json=sales_payload, headers=sales_rep_headers)
    assert sales_chat_resp.status_code == 200
    sales_data = sales_chat_resp.json()
    assert "access denied" in sales_data["answer"].lower()

    # 3. Verify actual AuditLog records were persisted in PostgreSQL
    audit_stmt = select(AuditLog).where(AuditLog.outcome == "deny").order_by(AuditLog.id.desc())
    denial_logs = (await db_session.execute(audit_stmt)).scalars().all()
    assert len(denial_logs) >= 2, "Real denial audit records must be saved in the database"
    actions = [log.action for log in denial_logs]
    assert any("denial" in a.lower() for a in actions)


@pytest.mark.asyncio
async def test_federation_gateway_field_filtering_and_audit(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict
):
    """
    Verify Scenario B: Sales querying Finance status via Federation Gateway.
    - Returns permitted opportunity finance status fields.
    - Prohibits forbidden fields (e.g. salary/profit margin).
    - Logs Gateway audit decisions into PostgreSQL.
    """
    payload = {"message": "Which opportunities are awaiting finance approval?"}
    resp = await async_client.post("/api/v1/chat", json=payload, headers=sales_rep_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "sales"
    assert len(data["evidence"]) > 0

    # Ensure no leaked sensitive finance details like general ledger or bank accounts
    for ev in data["evidence"]:
        assert "bank_account" not in ev["snippet"].lower()
        assert "profit_margin" not in ev["snippet"].lower()

    # Verify Gateway audit event exists in PostgreSQL
    stmt = select(AuditLog).where(AuditLog.action == "gateway:federated_request")
    gw_logs = (await db_session.execute(stmt)).scalars().all()
    assert len(gw_logs) > 0, "Gateway invocation must be audited in the database"
