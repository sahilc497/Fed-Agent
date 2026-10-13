import os
import sys
from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.main import app
from app.db.session import get_db
from app.core.security import create_access_token
from app.services.ollama_service import OllamaService

# Use NullPool for tests to guarantee each test gets a fresh connection
# and closes it cleanly within its own asyncio event loop
test_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


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


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


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


@pytest.fixture
def sales_manager_headers():
    return generate_auth_headers(3, "sales.manager@mesh.enterprise.internal", "department_manager", 1, "sales")


@pytest.fixture
def sales_rep_headers():
    return generate_auth_headers(4, "sales.rep@mesh.enterprise.internal", "department_employee", 1, "sales")


@pytest.fixture
def hr_manager_headers():
    return generate_auth_headers(5, "hr.manager@mesh.enterprise.internal", "department_manager", 2, "hr")


@pytest.fixture
def hr_specialist_headers():
    return generate_auth_headers(6, "hr.specialist@mesh.enterprise.internal", "department_employee", 2, "hr")


@pytest.fixture
def finance_manager_headers():
    return generate_auth_headers(7, "finance.manager@mesh.enterprise.internal", "department_manager", 3, "finance")


@pytest.fixture
def finance_analyst_headers():
    return generate_auth_headers(8, "finance.analyst@mesh.enterprise.internal", "department_employee", 3, "finance")


@pytest.fixture
def operations_manager_headers():
    return generate_auth_headers(9, "operations.manager@mesh.enterprise.internal", "department_manager", 4, "operations")


@pytest.fixture
def operations_lead_headers():
    return generate_auth_headers(10, "operations.lead@mesh.enterprise.internal", "department_employee", 4, "operations")


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

