import uuid
import datetime
import pytest
import httpx
from app.db.session import AsyncSession


@pytest.mark.asyncio
async def test_cross_dept_federation_chat_end_to_end_lifecycle(
    async_client: httpx.AsyncClient,
    db_session: AsyncSession,
    sales_rep_headers: dict,
    admin_headers: dict
):
    """
    End-to-End Test for User Workflow:
    1. Sales user chats asking for HR employee info before requesting -> Denied with Federation prompt.
    2. Sales user submits a cross-department request for HR.
    3. Sales user chats while request is PENDING -> Response explains request is awaiting Admin approval.
    4. Admin approves the request for 60 minutes.
    5. Sales user chats -> Successfully receives authorized HR department information and evidence.
    6. Sales user queries again -> Still succeeds while within the 60-minute time limit.
    7. Admin revokes the grant -> Sales user chat is immediately denied with Revocation notice.
    8. Expiration check -> An expired grant is denied with Expiration notice.
    """
    # 0. Clean slate for test isolation
    conn = getattr(db_session, "conn", db_session)
    conn.execute("DELETE FROM federation_access_requests;")
    await db_session.commit()

    # 1. Before requesting: Sales rep chats asking for HR employee info
    chat_payload = {"message": "Can you show me the HR leave policy and employee details?"}
    res_before = await async_client.post("/api/v1/chat", json=chat_payload, headers=sales_rep_headers)
    assert res_before.status_code == 200
    data_before = res_before.json()
    assert "access denied" in data_before["answer"].lower()
    assert "prohibited" in data_before["answer"].lower() or "submit a federation" in data_before["answer"].lower()

    # 2. Sales rep submits cross-department Federation Access Request for HR
    req_key = str(uuid.uuid4())
    create_payload = {
        "source_department_code": "hr",
        "business_purpose": "Staffing allocation for enterprise client deal",
        "requested_fields": ["full_name", "position", "leave_balance"],
        "record_identifiers": [],
        "access_duration_minutes": 60,
        "idempotency_key": req_key
    }
    res_create = await async_client.post("/api/v1/federation/requests", json=create_payload, headers=sales_rep_headers)
    assert res_create.status_code == 200
    req_data = res_create.json()
    req_id = req_data["id"]
    assert req_data["status"] == "PENDING"

    # 3. Sales rep chats while request is PENDING
    res_pending_chat = await async_client.post("/api/v1/chat", json=chat_payload, headers=sales_rep_headers)
    assert res_pending_chat.status_code == 200
    data_pending = res_pending_chat.json()
    assert "pending" in data_pending["answer"].lower()
    assert req_id[:8] in data_pending["answer"]
    assert "administrator approval" in data_pending["answer"].lower()

    # 4. Admin approves the Federation request
    res_approve = await async_client.post(
        f"/api/v1/federation/requests/{req_id}/decision",
        json={
            "decision": "approve",
            "reason": "Authorized for enterprise client deal staffing",
            "approved_fields": ["full_name", "position", "leave_balance"]
        },
        headers=admin_headers
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "APPROVED"

    # 5. Sales rep chats while grant is APPROVED -> Successfully retrieves HR records/evidence!
    res_approved_chat = await async_client.post("/api/v1/chat", json=chat_payload, headers=sales_rep_headers)
    assert res_approved_chat.status_code == 200
    data_approved = res_approved_chat.json()
    # Check that grant notice badge is present
    assert f"Approved Grant #{req_id[:8]}" in data_approved["answer"]
    # Check that authorized HR evidence was retrieved
    assert len(data_approved["evidence"]) > 0
    hr_snippets = [e["snippet"] for e in data_approved["evidence"] if e["department"] == "hr"]
    assert len(hr_snippets) > 0, "HR department evidence must be retrieved for Sales user"
    # Verify sensitive employee salary figures are strictly excluded
    for e in data_approved["evidence"]:
        if e["source_type"] == "business_record":
            assert "base salary: $" not in e["snippet"].lower()

    # 6. Sales rep chats again -> continues to succeed during the time limit
    query_2 = {"message": "Who is working in HR and what are their positions?"}
    res_chat_2 = await async_client.post("/api/v1/chat", json=query_2, headers=sales_rep_headers)
    assert res_chat_2.status_code == 200
    data_chat_2 = res_chat_2.json()
    assert f"Approved Grant #{req_id[:8]}" in data_chat_2["answer"]

    # 7. Admin revokes the grant
    res_revoke = await async_client.post(
        f"/api/v1/federation/requests/{req_id}/revoke",
        params={"reason": "Staffing exercise completed early"},
        headers=admin_headers
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["status"] == "REVOKED"

    # Sales rep chats after revocation -> Immediately denied!
    res_revoked_chat = await async_client.post("/api/v1/chat", json=chat_payload, headers=sales_rep_headers)
    assert res_revoked_chat.status_code == 200
    data_revoked = res_revoked_chat.json()
    assert "revoked" in data_revoked["answer"].lower()
    assert req_id[:8] in data_revoked["answer"]

    # 8. Test Expiration behavior
    # Create another request, approve it, and set expires_at in the past
    key_exp = str(uuid.uuid4())
    create_exp_payload = {
        "source_department_code": "hr",
        "business_purpose": "Expiry test",
        "requested_fields": ["full_name"],
        "idempotency_key": key_exp
    }
    r_exp_create = await async_client.post("/api/v1/federation/requests", json=create_exp_payload, headers=sales_rep_headers)
    exp_req_id = r_exp_create.json()["id"]

    await async_client.post(
        f"/api/v1/federation/requests/{exp_req_id}/decision",
        json={"decision": "approve", "reason": "Pre-approved for expiration test"},
        headers=admin_headers
    )

    # Artificially expire the grant in SQLite
    past_iso = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat()
    conn = getattr(db_session, "conn", db_session)
    conn.execute("UPDATE federation_access_requests SET expires_at = ? WHERE id = ?;", (past_iso, exp_req_id))
    await db_session.commit()

    # Sales rep chats -> Denied with expiration notice!
    res_expired_chat = await async_client.post("/api/v1/chat", json=chat_payload, headers=sales_rep_headers)
    assert res_expired_chat.status_code == 200
    data_expired = res_expired_chat.json()
    assert "expired" in data_expired["answer"].lower()
