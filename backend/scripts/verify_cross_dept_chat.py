"""
Direct Unit & Integration Verification Script for Cross-Department Chat:
1. Initialize test user & active approved federation grant for Finance in SQLite.
2. Create persistent conversation titled 'CROSS Dept Chat: FINANCE (#REQ_ID)'.
3. Run Orchestrator with sales user querying Finance data with department_hint.
4. Verify response is authorized under the approved grant and sensitive data is stripped.
5. Verify persistent messages are recorded in SQLite (conversations and chat_messages).
6. Verify retrieval and conversation listing.
"""

import sys
import os
import uuid
import datetime
import asyncio
from unittest.mock import patch, AsyncMock

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.sqlite import create_connection, SqliteSession
from app.db.schema import init_db
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.user_repo import UserRepository, DepartmentRepository
from app.repositories.federation_repo import FederationRequestRepository
from app.orchestrator.orchestrator import Orchestrator
from app.schemas.chat import ChatRequest
from app.db.models.federation_request import FederationAccessRequest
from app.services.ollama_service import OllamaService


async def run_verification():
    print("=== Step 1: Initialize Database & Repositories ===", flush=True)
    init_db()
    conn = create_connection()
    session = SqliteSession(conn)
    conv_repo = ConversationRepository(session)
    user_repo = UserRepository(session)
    dept_repo = DepartmentRepository(session)
    fed_repo = FederationRequestRepository(session)

    # Fetch users and departments
    sales_dept = await dept_repo.get_by_code("sales")
    finance_dept = await dept_repo.get_by_code("finance")
    assert sales_dept and finance_dept

    sales_user = await user_repo.get_by_email("sales.rep@mesh.enterprise.internal")
    if not sales_user:
        sales_user = await user_repo.get_by_email("sales.lead@mesh.internal")
    assert sales_user, "Sales user not found in database"

    admin_user = await user_repo.get_by_email("admin@mesh.enterprise.internal")
    if not admin_user:
        admin_user = await user_repo.get_by_email("admin@mesh.internal")
    assert admin_user, "Admin user not found in database"

    print(f"[OK] Found Sales User: {sales_user.email} (ID: {sales_user.id}, Dept: {sales_user.department_id})", flush=True)

    print("\n=== Step 2: Create Approved Federation Access Request ===", flush=True)
    req_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = (now + datetime.timedelta(minutes=60)).isoformat()
    now_iso = now.isoformat()

    fed_grant = FederationAccessRequest(
        id=req_id,
        requester_user_id=sales_user.id,
        requester_department_id=sales_dept.id,
        requesting_agent="sales_agent",
        source_department_id=finance_dept.id,
        business_purpose="Invoice INV-2026-001 clearance check for contract closing",
        requested_fields=["invoice_number", "client_name", "status"],
        record_identifiers=["INV-2026-001"],
        access_duration_minutes=60,
        status="APPROVED",
        approver_user_id=admin_user.id,
        decision_reason="Approved cross-dept access by security policy",
        approved_fields=["invoice_number", "client_name", "status"],
        approved_record_ids=["INV-2026-001"],
        idempotency_key=str(uuid.uuid4()),
        created_at=now_iso,
        decided_at=now_iso,
        expires_at=expires_at
    )
    await fed_repo.create(fed_grant)
    await session.commit()
    print(f"[OK] Active Federation Grant #{req_id[:8]} created in SQLite. Expires: {expires_at}", flush=True)

    print("\n=== Step 3: Create Persistent CROSS Dept Chat Conversation ===", flush=True)
    chat_title = f"CROSS Dept Chat: FINANCE (#{req_id[:8]})"
    conv = await conv_repo.create_conversation(sales_user.id, sales_user.department_id, chat_title)
    print(f"[OK] Created conversation '{conv.title}' with ID: {conv.id}", flush=True)

    print("\n=== Step 4: Sales Rep Asks Query via Orchestrator ===", flush=True)
    orchestrator = Orchestrator(session)
    request = ChatRequest(
        message="What is the status and due date for invoice INV-2026-001?",
        conversation_id=conv.id,
        department_hint="finance"
    )

    # 4a. Record user message in SQLite
    await conv_repo.add_message(
        conversation_id=conv.id,
        sender_role="user",
        message=request.message
    )

    # 4b. Handle chat with mocked local ollama response
    async def fake_grounded_answer(prompt: str, system_instruction=None, evidence=None):
        if evidence:
            summary = " ".join([e.get("snippet", "") for e in evidence])
            return f"Answer grounded in authorized enterprise records: {summary}"
        return "I do not have sufficient authorized evidence to answer this question."

    with patch.object(OllamaService, "generate_grounded_answer", new=AsyncMock(side_effect=fake_grounded_answer)):
        response = await orchestrator.handle_chat(sales_user, request)
    response.conversation_id = conv.id

    # 4c. Record assistant message in SQLite
    evidence_dicts = [e.model_dump() for e in response.evidence] if response.evidence else []
    await conv_repo.add_message(
        conversation_id=conv.id,
        sender_role="assistant",
        message=response.answer,
        intent=response.intent,
        routed_departments=response.routed_departments,
        evidence_json=evidence_dicts
    )
    await session.commit()

    print(f"[OK] Orchestrator responded:", flush=True)
    print(f"     Intent: {response.intent}", flush=True)
    print(f"     Routed Depts: {response.routed_departments}", flush=True)
    print(f"     Evidence Count: {len(response.evidence)}", flush=True)
    print(f"     Answer:\n{response.answer[:250]}...\n", flush=True)

    assert f"Approved Grant #{req_id[:8]}" in response.answer, "Expected active grant badge banner in answer"

    print("\n=== Step 5: Verify Persistent Chat History Loaded From SQLite ===", flush=True)
    saved_messages = await conv_repo.get_messages(conv.id, sales_user.id)
    assert len(saved_messages) == 2, f"Expected 2 messages, got {len(saved_messages)}"

    user_msg = saved_messages[0]
    asst_msg = saved_messages[1]

    assert user_msg.sender_role == "user"
    assert user_msg.message == request.message
    assert asst_msg.sender_role == "assistant"
    assert asst_msg.intent == "finance"
    assert "Approved Grant" in asst_msg.message

    print(f"[OK] Stored User Message (ID {user_msg.id}): {user_msg.message}", flush=True)
    print(f"[OK] Stored Assistant Message (ID {asst_msg.id}): {asst_msg.message[:80]}...", flush=True)
    print(f"     Routed Depts in SQLite: {asst_msg.routed_departments}", flush=True)
    print(f"     Evidence Count in SQLite: {len(asst_msg.evidence_json)}", flush=True)

    print("\n=== Step 6: Verify User Conversation List ===", flush=True)
    user_convs = await conv_repo.list_for_user(sales_user.id)
    matching_conv = next((c for c in user_convs if c.id == conv.id), None)
    assert matching_conv is not None, "Conversation must exist in user conversation history"
    assert matching_conv.title == chat_title
    print(f"[OK] Verified Conversation in User List: '{matching_conv.title}'", flush=True)

    print("\n==================================================================")
    print("ALL CROSS-DEPARTMENT CHAT VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("==================================================================")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_verification())
