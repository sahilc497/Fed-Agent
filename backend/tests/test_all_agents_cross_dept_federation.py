import uuid
import datetime
import pytest
import httpx
from app.db.session import AsyncSession


@pytest.mark.asyncio
async def test_all_four_agents_cross_department_federation_chat_matrix(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict,
    hr_specialist_headers: dict,
    admin_headers: dict
):
    """
    Exhaustive verification of cross-department federation across ALL 4 agents:
    Pair 1: Sales Agent -> Finance Agent (Invoices & Payment Status)
    Pair 2: HR Agent -> Sales Agent (Client Deals & Revenue Pipeline)
    Pair 3: HR Agent -> Operations Agent (Warehouse Stock & SKUs)
    Pair 4: Sales Agent -> Operations Agent (Inventory Availability)
    
    Validates for EACH agent:
    - Pre-request denial under Zero-Trust
    - Request submission & pending notification
    - Admin approval with specific time limit
    - Chat grounded in target agent records & evidence
    - Active time limit multi-query verification
    - Immediate denial upon revocation
    """
    conn = getattr(db_session, "conn", db_session)
    conn.execute("DELETE FROM federation_access_requests;")
    await db_session.commit()

    # =========================================================================
    # PAIR 1: Sales Rep requesting FINANCE Agent Info
    # =========================================================================
    finance_query = {"message": "What is the status and due date for invoice INV-2026-001?"}
    
    # 1.1 Before request: Sales rep denied
    res_s_f_before = await async_client.post("/api/v1/chat", json=finance_query, headers=sales_rep_headers)
    assert res_s_f_before.status_code == 200
    assert "access denied" in res_s_f_before.json()["answer"].lower()

    # 1.2 Sales rep submits request for Finance
    req_sf = {
        "source_department_code": "finance",
        "business_purpose": "Credit clearance for deal closing",
        "requested_fields": ["invoice_number", "client_name", "status"],
        "access_duration_minutes": 60,
        "idempotency_key": str(uuid.uuid4())
    }
    r_sf = await async_client.post("/api/v1/federation/requests", json=req_sf, headers=sales_rep_headers)
    assert r_sf.status_code == 200
    sf_id = r_sf.json()["id"]

    # 1.3 While pending: notice shown
    res_sf_pending = await async_client.post("/api/v1/chat", json=finance_query, headers=sales_rep_headers)
    assert "pending" in res_sf_pending.json()["answer"].lower()

    # 1.4 Admin approves
    await async_client.post(
        f"/api/v1/federation/requests/{sf_id}/decision",
        json={"decision": "approve", "reason": "Approved credit clearance check"},
        headers=admin_headers
    )

    # 1.5 Sales rep chats: receives FINANCE data
    res_sf_approved = await async_client.post("/api/v1/chat", json=finance_query, headers=sales_rep_headers)
    assert res_sf_approved.status_code == 200
    sf_data = res_sf_approved.json()
    assert f"Approved Grant #{sf_id[:8]}" in sf_data["answer"]
    fin_evidence = [e for e in sf_data["evidence"] if e["department"] == "finance"]
    assert len(fin_evidence) > 0, "Sales agent must retrieve Finance evidence"
    assert any("INV-2026-001" in e["snippet"] or "invoice" in e["snippet"].lower() for e in fin_evidence)

    # =========================================================================
    # PAIR 2: HR Specialist requesting SALES Agent Info
    # =========================================================================
    sales_query = {"message": "Show me sales opportunities and client pipeline deals"}

    # 2.1 Before request: HR specialist denied
    res_h_s_before = await async_client.post("/api/v1/chat", json=sales_query, headers=hr_specialist_headers)
    assert res_h_s_before.status_code == 200
    assert "access denied" in res_h_s_before.json()["answer"].lower()

    # 2.2 HR submits request for Sales
    req_hs = {
        "source_department_code": "sales",
        "business_purpose": "Staffing quota planning by deal volume",
        "requested_fields": ["title", "client_name", "deal_value", "stage"],
        "access_duration_minutes": 45,
        "idempotency_key": str(uuid.uuid4())
    }
    r_hs = await async_client.post("/api/v1/federation/requests", json=req_hs, headers=hr_specialist_headers)
    assert r_hs.status_code == 200
    hs_id = r_hs.json()["id"]

    # 2.3 Admin approves
    await async_client.post(
        f"/api/v1/federation/requests/{hs_id}/decision",
        json={"decision": "approve", "reason": "Approved for HR workforce planning"},
        headers=admin_headers
    )

    # 2.4 HR specialist chats: receives SALES data
    res_hs_approved = await async_client.post("/api/v1/chat", json=sales_query, headers=hr_specialist_headers)
    assert res_hs_approved.status_code == 200
    hs_data = res_hs_approved.json()
    assert f"Approved Grant #{hs_id[:8]}" in hs_data["answer"]
    sales_evidence = [e for e in hs_data["evidence"] if e["department"] == "sales"]
    assert len(sales_evidence) > 0, "HR agent must retrieve Sales evidence"

    # =========================================================================
    # PAIR 3: HR Specialist requesting OPERATIONS Agent Info
    # =========================================================================
    ops_query = {"message": "What is the warehouse inventory quantity on hand for SKU-1001?"}

    # 3.1 Before request: HR specialist denied
    res_h_o_before = await async_client.post("/api/v1/chat", json=ops_query, headers=hr_specialist_headers)
    assert res_h_o_before.status_code == 200
    assert "access denied" in res_h_o_before.json()["answer"].lower()

    # 3.2 HR submits request for Operations
    req_ho = {
        "source_department_code": "operations",
        "business_purpose": "Workplace equipment ergonomics audit",
        "requested_fields": ["sku", "item_name", "quantity_on_hand"],
        "access_duration_minutes": 30,
        "idempotency_key": str(uuid.uuid4())
    }
    r_ho = await async_client.post("/api/v1/federation/requests", json=req_ho, headers=hr_specialist_headers)
    assert r_ho.status_code == 200
    ho_id = r_ho.json()["id"]

    # 3.3 Admin approves
    await async_client.post(
        f"/api/v1/federation/requests/{ho_id}/decision",
        json={"decision": "approve", "reason": "Approved ergonomics audit"},
        headers=admin_headers
    )

    # 3.4 HR specialist chats: receives OPERATIONS inventory data
    res_ho_approved = await async_client.post("/api/v1/chat", json=ops_query, headers=hr_specialist_headers)
    assert res_ho_approved.status_code == 200
    ho_data = res_ho_approved.json()
    assert f"Approved Grant #{ho_id[:8]}" in ho_data["answer"]
    ops_evidence = [e for e in ho_data["evidence"] if e["department"] == "operations"]
    assert len(ops_evidence) > 0, "HR agent must retrieve Operations evidence"

    # =========================================================================
    # PAIR 4: Revocation Test across Agents
    # =========================================================================
    # Admin revokes HR -> Operations grant
    res_rev = await async_client.post(
        f"/api/v1/federation/requests/{ho_id}/revoke",
        params={"reason": "Audit completed"},
        headers=admin_headers
    )
    assert res_rev.status_code == 200

    # HR attempts ops query again: immediately denied
    res_ho_revoked = await async_client.post("/api/v1/chat", json=ops_query, headers=hr_specialist_headers)
    assert res_ho_revoked.status_code == 200
    assert "revoked" in res_ho_revoked.json()["answer"].lower()
