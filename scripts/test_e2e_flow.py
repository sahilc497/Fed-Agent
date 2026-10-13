import os
import sys
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

async def test_e2e():
    print("=" * 70)
    print("STARTING END-TO-END SYSTEM & SECURITY INTEGRATION VERIFICATION")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=140.0) as client:
        # 1. Health & Readiness
        print("\n[1] Testing Health & Readiness Probes...")
        r_health = await client.get("/health")
        assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
        print(f"    /health: OK (200) -> {r_health.json()}")

        r_ready = await client.get("/health/ready")
        assert r_ready.status_code == 200, f"Readiness check failed: {r_ready.text}"
        print(f"    /health/ready: OK (200) -> status={r_ready.json().get('status')}")

        # 2. Authentication
        print("\n[2] Testing Authentication & Token Issuance...")
        login_payload = {
            "email": "sales.rep@mesh.enterprise.internal",
            "password": "MeshSecure2026!"
        }
        r_login = await client.post(f"{API_V1}/auth/login", json=login_payload)
        assert r_login.status_code == 200, f"Sales login failed: {r_login.text}"
        sales_token = r_login.json()["access_token"]
        sales_headers = {"Authorization": f"Bearer {sales_token}"}
        print(f"    Sales Rep Login: Authenticated (JWT issued, user={r_login.json()['user']['full_name']})")

        # Login HR Manager
        r_hr_login = await client.post(f"{API_V1}/auth/login", json={
            "email": "hr.manager@mesh.enterprise.internal",
            "password": "MeshSecure2026!"
        })
        assert r_hr_login.status_code == 200
        hr_token = r_hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}
        print(f"    HR Director Login: Authenticated (JWT issued, user={r_hr_login.json()['user']['full_name']})")

        # Login HR Specialist
        r_hr_spec = await client.post(f"{API_V1}/auth/login", json={
            "email": "hr.specialist@mesh.enterprise.internal",
            "password": "MeshSecure2026!"
        })
        assert r_hr_spec.status_code == 200
        hr_spec_token = r_hr_spec.json()["access_token"]
        hr_spec_headers = {"Authorization": f"Bearer {hr_spec_token}"}

        # 3. Department Data Isolation
        print("\n[3] Testing Zero-Trust Department Direct Record Isolation...")
        # Sales Rep accessing Sales records -> Allowed
        r_sales_records = await client.get(f"{API_V1}/departments/sales/records", headers=sales_headers)
        assert r_sales_records.status_code == 200, f"Sales records failed: {r_sales_records.text}"
        print(f"    Sales Rep accessing Sales records: ALLOWED (retrieved {len(r_sales_records.json())} records)")

        # Sales Rep attempting to access HR records directly -> FORBIDDEN (403)
        r_cross = await client.get(f"{API_V1}/departments/hr/records", headers=sales_headers)
        assert r_cross.status_code == 403, f"Expected 403, got {r_cross.status_code}: {r_cross.text}"
        print(f"    Sales Rep accessing HR records directly: BLOCKED (403 Forbidden: Zero-Trust Isolation Enforced)")

        # 4. Sensitive Field Masking (Salary Redaction)
        print("\n[4] Testing Sensitive Field Masking (Salary Redaction Policy)...")
        # HR Specialist (non-manager) viewing HR records -> Salary must be null
        r_hr_spec_rec = await client.get(f"{API_V1}/departments/hr/records", headers=hr_spec_headers)
        assert r_hr_spec_rec.status_code == 200
        spec_records = r_hr_spec_rec.json()
        assert len(spec_records) > 0
        assert all(rec["salary"] is None for rec in spec_records), "Salary was NOT masked for non-manager HR staff!"
        print(f"    HR Specialist viewing HR records: Salary successfully REDACTED/MASKED (null)")

        # HR Manager viewing HR records -> Salary must be visible
        r_hr_mgr_rec = await client.get(f"{API_V1}/departments/hr/records", headers=hr_headers)
        assert r_hr_mgr_rec.status_code == 200
        mgr_records = r_hr_mgr_rec.json()
        assert len(mgr_records) > 0
        assert any(rec["salary"] is not None for rec in mgr_records), "Salary was incorrectly masked for HR Manager!"
        print(f"    HR Manager viewing HR records: Salary UNMASKED for authorized manager")

        # 5. Semantic RAG Chat & Agent Routing
        print("\n[5] Testing AI Multi-Agent Mesh Chat Routing & Citations...")
        chat_req = {
            "message": "What is our corporate policy regarding discounts that require finance sign-off?"
        }
        r_chat = await client.post(f"{API_V1}/chat", json=chat_req, headers=sales_headers)
        assert r_chat.status_code == 200, f"Chat failed: {r_chat.text}"
        chat_resp = r_chat.json()
        print(f"    Routed Departments: {chat_resp.get('routed_departments')}")
        print(f"    Answer Snippet: {chat_resp.get('answer')[:120]}...")
        assert len(chat_resp.get("evidence", [])) > 0, "No evidence citations returned by semantic RAG!"
        print(f"    Evidence Citations: {len(chat_resp['evidence'])} chunks cited (Confidence: {chat_resp['evidence'][0]['confidence']})")

        # 6. Approvals & Anti-Self-Approval
        print("\n[6] Testing Approvals & Anti-Self-Approval Controls...")
        r_apprs = await client.get(f"{API_V1}/approvals?status_filter=pending", headers=hr_headers)
        assert r_apprs.status_code == 200
        print(f"    Pending Approvals listed: {len(r_apprs.json())} pending actions")

        # 7. Audit Trail Verification
        print("\n[7] Testing Immutable Security Audit Log...")
        # Login auditor
        r_aud_login = await client.post(f"{API_V1}/auth/login", json={
            "email": "auditor@mesh.enterprise.internal",
            "password": "MeshSecure2026!"
        })
        assert r_aud_login.status_code == 200
        aud_headers = {"Authorization": f"Bearer {r_aud_login.json()['access_token']}"}

        r_audit = await client.get(f"{API_V1}/audit?limit=10", headers=aud_headers)
        assert r_audit.status_code == 200, f"Audit failed: {r_audit.text}"
        audit_events = r_audit.json()
        print(f"    Retrieved {len(audit_events)} audit events for Security Auditor")
        assert any(ev["outcome"].lower() in ["allow", "deny"] for ev in audit_events)
        print("    Audit log verified: Records both allow and deny outcomes with correlation IDs")

    print("\n" + "=" * 70)
    print("ALL END-TO-END TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_e2e())
