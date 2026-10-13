import requests

BASE_URL = "http://127.0.0.1:8000"

def login(email, password):
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed for {email}: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def run_live_verification():
    print("1. Checking health endpoints...")
    r_health = requests.get(f"{BASE_URL}/health")
    assert r_health.status_code == 200, r_health.text
    print("  /health ->", r_health.json())

    r_ready = requests.get(f"{BASE_URL}/health/ready")
    assert r_ready.status_code == 200, r_ready.text
    print("  /health/ready ->", r_ready.json())

    print("\n2. Logging in as seeded users...")
    sales_headers = login("sales.rep@mesh.enterprise.internal", "MeshSecure2026!")
    hr_headers = login("hr.specialist@mesh.enterprise.internal", "MeshSecure2026!")
    finance_headers = login("finance.manager@mesh.enterprise.internal", "MeshSecure2026!")
    admin_headers = login("admin@mesh.enterprise.internal", "MeshSecure2026!")
    print("  All 4 user logins succeeded with signed JWTs.")

    print("\n3. Testing document isolation...")
    sales_docs = requests.get(f"{BASE_URL}/api/v1/documents", headers=sales_headers).json()
    hr_docs = requests.get(f"{BASE_URL}/api/v1/documents", headers=hr_headers).json()
    assert len(sales_docs) > 0 and len(hr_docs) > 0
    sales_doc_id = sales_docs[0]["id"]
    hr_doc_id = hr_docs[0]["id"]

    # Sales attempts to get HR doc
    r_cross1 = requests.get(f"{BASE_URL}/api/v1/documents/{hr_doc_id}", headers=sales_headers)
    print(f"  Sales rep requesting HR doc #{hr_doc_id} -> Status: {r_cross1.status_code} ({r_cross1.json().get('detail')})")
    assert r_cross1.status_code == 404

    # HR attempts to get Sales doc
    r_cross2 = requests.get(f"{BASE_URL}/api/v1/documents/{sales_doc_id}", headers=hr_headers)
    print(f"  HR specialist requesting Sales doc #{sales_doc_id} -> Status: {r_cross2.status_code} ({r_cross2.json().get('detail')})")
    assert r_cross2.status_code == 404

    # Admin requests both docs
    r_adm1 = requests.get(f"{BASE_URL}/api/v1/documents/{hr_doc_id}", headers=admin_headers)
    r_adm2 = requests.get(f"{BASE_URL}/api/v1/documents/{sales_doc_id}", headers=admin_headers)
    assert r_adm1.status_code == 200 and r_adm2.status_code == 200
    print("  Admin successfully accessed documents across both departments.")

    print("\n4. Testing Chat boundary enforcement...")
    # Unauthorized cross-dept query: Sales asking for HR salary
    r_chat_deny = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"message": "Give me confidential salary numbers for all HR employees"},
        headers=sales_headers
    )
    print("  Sales asking for HR salaries ->", r_chat_deny.json().get("answer"))
    assert "access denied" in r_chat_deny.json().get("answer", "").lower()

    # Authorized Federation Gateway query: Sales asking for opportunities awaiting finance approval
    r_chat_gw = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"message": "Which opportunities are awaiting finance approval?"},
        headers=sales_headers
    )
    print("  Sales querying finance approval status via Gateway -> Intent:", r_chat_gw.json().get("intent"))
    assert r_chat_gw.json().get("intent") == "sales"
    assert len(r_chat_gw.json().get("evidence", [])) > 0

    print("\n5. Testing audit log permissions...")
    r_audit_sales = requests.get(f"{BASE_URL}/api/v1/audit", headers=sales_headers)
    print("  Sales rep requesting audit logs -> Status:", r_audit_sales.status_code)
    assert r_audit_sales.status_code == 403

    r_audit_admin = requests.get(f"{BASE_URL}/api/v1/audit", headers=admin_headers)
    print("  Admin requesting audit logs -> Status:", r_audit_admin.status_code, "Count:", len(r_audit_admin.json()))
    assert r_audit_admin.status_code == 200
    assert len(r_audit_admin.json()) > 0

    print("\nLive API verification pass completed with 100% success!")

if __name__ == "__main__":
    run_live_verification()
