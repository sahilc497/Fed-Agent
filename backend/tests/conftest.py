import os
import sys
from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.main import app
from app.db.sqlite import create_connection, SqliteSession
from app.db.session import get_db
from app.db.schema import init_db
from app.core.security import create_access_token
from app.services.ollama_service import OllamaService

# Ensure SQLite schema is initialized for test execution
init_db()


def override_get_db():
    conn = create_connection()
    session = SqliteSession(conn)
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def mock_ollama_for_unit_tests(request):
    """
    Mocks Ollama grounded answer generation for fast, deterministic unit and scenario testing.
    Actual Ollama integration is tested separately in test_ollama.py without mock.
    """
    if "test_ollama" in request.node.nodeid:
        yield
        return

    async def fake_grounded_answer(prompt: str, system_instruction=None, evidence=None):
        if evidence:
            summary = " ".join([e.get("snippet", "") for e in evidence])
            return f"Answer grounded in authorized enterprise records: {summary}"
        return "I do not have sufficient authorized evidence to answer this question."

    with patch.object(OllamaService, "generate_grounded_answer", new=AsyncMock(side_effect=fake_grounded_answer)):
        yield


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def db_session():
    conn = create_connection()
    session = SqliteSession(conn)
    try:
        yield session
    finally:
        session.close()


def generate_auth_headers(user_id: int, email: str, role: str, dept_id: int, dept_code: str) -> dict:
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


@pytest.fixture
def admin_headers():
    return generate_auth_headers(1, "admin@mesh.enterprise.internal", "admin", 3, "finance")


@pytest.fixture
def auditor_headers():
    return generate_auth_headers(2, "auditor@mesh.enterprise.internal", "auditor", 3, "finance")


def get_user_header_by_email(email: str) -> dict:
    conn = create_connection()
    row = conn.execute("SELECT id, email, role, department_id FROM users WHERE email = ?;", (email,)).fetchone()
    conn.close()
    if row:
        dept_code = "sales" if row["department_id"] == 1 else ("hr" if row["department_id"] == 2 else ("finance" if row["department_id"] == 3 else "operations"))
        return generate_auth_headers(row["id"], row["email"], row["role"], row["department_id"], dept_code)
    return {}


@pytest.fixture
def admin_headers():
    return get_user_header_by_email("admin@mesh.enterprise.internal")


@pytest.fixture
def sales_manager_headers():
    return get_user_header_by_email("sales.manager@mesh.enterprise.internal")


@pytest.fixture
def sales_rep_headers():
    return get_user_header_by_email("sales.rep@mesh.enterprise.internal")


@pytest.fixture
def hr_manager_headers():
    return get_user_header_by_email("hr.manager@mesh.enterprise.internal")


@pytest.fixture
def hr_specialist_headers():
    return get_user_header_by_email("hr.specialist@mesh.enterprise.internal")


@pytest.fixture
def finance_manager_headers():
    return get_user_header_by_email("finance.manager@mesh.enterprise.internal")


@pytest.fixture
def finance_analyst_headers():
    return get_user_header_by_email("finance.analyst@mesh.enterprise.internal")


@pytest.fixture
def operations_manager_headers():
    return get_user_header_by_email("operations.manager@mesh.enterprise.internal")


@pytest.fixture
def operations_lead_headers():
    return get_user_header_by_email("operations.lead@mesh.enterprise.internal")


@pytest_asyncio.fixture
async def admin_user(db_session):
    from app.repositories.user_repo import UserRepository
    repo = UserRepository(db_session)
    return await repo.get_by_email("admin@mesh.enterprise.internal")


@pytest_asyncio.fixture
async def sales_user(db_session):
    from app.repositories.user_repo import UserRepository
    repo = UserRepository(db_session)
    return await repo.get_by_email("sales.rep@mesh.enterprise.internal")


@pytest_asyncio.fixture
async def hr_user(db_session):
    from app.repositories.user_repo import UserRepository
    repo = UserRepository(db_session)
    return await repo.get_by_email("hr.specialist@mesh.enterprise.internal")


@pytest_asyncio.fixture
async def finance_user(db_session):
    from app.repositories.user_repo import UserRepository
    repo = UserRepository(db_session)
    return await repo.get_by_email("finance.analyst@mesh.enterprise.internal")


@pytest_asyncio.fixture
async def operations_user(db_session):
    from app.repositories.user_repo import UserRepository
    repo = UserRepository(db_session)
    return await repo.get_by_email("operations.lead@mesh.enterprise.internal")

