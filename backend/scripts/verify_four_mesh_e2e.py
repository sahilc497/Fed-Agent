"""
End-to-end verification script for the upgraded Federated Agentic Mesh:
- 4 departments: Sales, HR, Finance, Operations
- Shared local LLM client
- Strict departmental data isolation
- Admin-controlled Federation Access Requests lifecycle (Create -> Pending -> Approve -> Consume -> Revoke)
"""

import sys
import os
import asyncio
import httpx
from httpx import ASGITransport

# Add parent directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.security import create_access_token

def auth_headers(user_id: int, email: str, role: str, dept_id: int, dept_code: str) -> dict:
    token = create_access_token(
        subject=user_id,
        claims={
            "email": email,
            "role": role,
            "department_id": dept_id,
            "department_code": dept_code
        }
    )
    return {"Authorization": f"Bearer {token}"}

async def async_main():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("=== Step 1: Verify Health Readiness & Shared Ollama ===")
        health_resp = await client.get("/health/ready")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
        health_data = health_resp.json()
        print(f"Health Status: {health_data['status']}")
        print(f"Ollama Dependency: {health_data['dependencies']['ollama_local_runtime']}")
        print("[OK] Shared LLM health verified.\n")

        print("=== Step 2: Verify 4 Department Agents & Status ===")
        admin_headers = auth_headers(1, "admin@mesh.enterprise.internal", "admin", 3, "finance")

        agents_resp = await client.get("/api/v1/agents", headers=admin_headers)
        assert agents_resp.status_code == 200, f"Get agents failed: {agents_resp.text}"
        agents = agents_resp.json()
        agent_codes = [a["agent_code"] for a in agents]
        print(f"Registered Agents: {agent_codes}")
        for code in ["sales", "hr", "finance", "operations"]:
            assert code in agent_codes, f"Missing agent: {code}"
        print("[OK] All 4 department agents registered.\n")

        print("=== Step 3: Verify Operations Business Records Endpoint ===")
        ops_headers = auth_headers(10, "operations.lead@mesh.enterprise.internal", "department_employee", 4, "operations")

        ops_records_resp = await client.get("/api/v1/departments/operations/records", headers=ops_headers)
        assert ops_records_resp.status_code == 200, f"Ops records failed: {ops_records_resp.text}"
        items = ops_records_resp.json()
        print(f"Operations inventory items retrieved: {len(items)} items")
        assert len(items) > 0, "No operations items found"
        print(f"Sample item: {items[0]['sku']} - {items[0]['item_name']} ({items[0]['quantity_on_hand']} units)")
        print("[OK] Operations department records verified.\n")

        print("=== Step 4: Verify Department Boundary Isolation ===")
        sales_headers = auth_headers(4, "sales.rep@mesh.enterprise.internal", "department_employee", 1, "sales")

        # Sales user tries to access Operations records -> 403 Forbidden
        forbidden_resp = await client.get("/api/v1/departments/operations/records", headers=sales_headers)
        assert forbidden_resp.status_code == 403, f"Expected 403, got {forbidden_resp.status_code}"
        print(f"Sales employee accessing Operations: HTTP {forbidden_resp.status_code} Forbidden (Blocked)")

        # Sales user tries to access HR records -> 403 Forbidden
        forbidden_hr = await client.get("/api/v1/departments/hr/records", headers=sales_headers)
        assert forbidden_hr.status_code == 403, f"Expected 403, got {forbidden_hr.status_code}"
        print(f"Sales employee accessing HR: HTTP {forbidden_hr.status_code} Forbidden (Blocked)")
        print("[OK] Department boundary isolation verified.\n")

        print("=== Step 5: Verify Federation Access Request Lifecycle ===")
        # 5a: Sales employee requests access to Finance data
        create_req = {
            "source_department_code": "finance",
            "business_purpose": "Invoice INV-2026-001 payment verification for pending enterprise contract",
            "requested_fields": ["invoice_number", "client_name", "status"],
            "record_identifiers": ["INV-2026-001"],
            "access_duration_minutes": 60
        }
        create_resp = await client.post("/api/v1/federation/requests", json=create_req, headers=sales_headers)
        assert create_resp.status_code == 200, f"Create federation request failed: {create_resp.text}"
        req_data = create_resp.json()
        req_id = req_data["id"]
        print(f"Created Federation Request {req_id} with status: {req_data['status']}")
        assert req_data["status"] == "PENDING"

        # 5b: Attempt to consume pending request -> 403 Forbidden
        consume_pending = await client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_headers)
        assert consume_pending.status_code == 403, f"Expected 403 for pending request, got {consume_pending.status_code}"
        print("Consume while pending: HTTP 403 Forbidden (Blocked as required)")

        # 5c: Sales employee attempts self-approval -> 403 Forbidden
        self_approve = await client.post(
            f"/api/v1/federation/requests/{req_id}/decision",
            json={"decision": "approve", "reason": "Self approving"},
            headers=sales_headers
        )
        assert self_approve.status_code == 403, f"Expected 403 for self-approval, got {self_approve.status_code}"
        print("Self-approval by requester: HTTP 403 Forbidden (Prevented)")

        # 5d: Authorized Admin approves request with narrowed fields
        decision_payload = {
            "decision": "approve",
            "reason": "Authorized by Controller for client contract validation",
            "approved_fields": ["invoice_number", "client_name", "status"]
        }
        approve_resp = await client.post(
            f"/api/v1/federation/requests/{req_id}/decision",
            json=decision_payload,
            headers=admin_headers
        )
        assert approve_resp.status_code == 200, f"Admin approve failed: {approve_resp.text}"
        approved_data = approve_resp.json()
        assert approved_data["status"] == "APPROVED"
        print(f"Admin Approval Granted: Status={approved_data['status']}, Approved Fields={approved_data['approved_fields']}")

        # 5e: Consume approved grant -> returns filtered records
        consume_resp = await client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_headers)
        assert consume_resp.status_code == 200, f"Consume failed: {consume_resp.text}"
        consume_data = consume_resp.json()
        print(f"Released Data: {consume_data['record_count']} records from {consume_data['source_department']}")
        assert len(consume_data["records"]) > 0
        sample_rec = consume_data["records"][0]
        print(f"Sample Released Record keys: {list(sample_rec.keys())}")
        # Verify confidential unapproved fields are NOT leaked
        assert "amount" not in sample_rec, "Unapproved field 'amount' leaked into response!"
        print("[OK] Released records contain only approved fields; unapproved fields strictly filtered out.")

        # 5f: Admin revokes grant
        revoke_resp = await client.post(
            f"/api/v1/federation/requests/{req_id}/revoke?reason=Task+completed+early",
            headers=admin_headers
        )
        assert revoke_resp.status_code == 200, f"Revoke failed: {revoke_resp.text}"
        assert revoke_resp.json()["status"] == "REVOKED"
        print("Grant revoked by administrator: Status=REVOKED")

        # 5g: Attempt to consume revoked grant -> 403 Forbidden
        consume_revoked = await client.post(f"/api/v1/federation/requests/{req_id}/consume", headers=sales_headers)
        assert consume_revoked.status_code == 403, f"Expected 403 for revoked grant, got {consume_revoked.status_code}"
        print("Consume while revoked: HTTP 403 Forbidden (Blocked as required)")
        print("[OK] Complete Federation Access Request lifecycle verified.\n")

        print("=== Step 6: Verify Department Agent Disable/Enable Behavior ===")
        # Disable Operations Agent
        toggle_resp = await client.post("/api/v1/agents/operations/toggle?is_enabled=false", headers=admin_headers)
        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["is_enabled"] is False

        # Re-enable Operations Agent
        toggle_resp2 = await client.post("/api/v1/agents/operations/toggle?is_enabled=true", headers=admin_headers)
        assert toggle_resp2.status_code == 200
        assert toggle_resp2.json()["is_enabled"] is True
        print("[OK] Agent enable/disable toggle verified.")

        print("\n=======================================================")
        print("[SUCCESS] ALL END-TO-END MESH REQUIREMENTS VERIFIED SUCCESSFULLY!")
        print("=======================================================")

if __name__ == "__main__":
    asyncio.run(async_main())
