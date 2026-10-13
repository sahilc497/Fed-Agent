import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ollama_service import get_shared_ollama_service
from app.agents.sales_agent import SalesAgent
from app.agents.hr_agent import HRAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.operations_agent import OperationsAgent
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.router_interface import RuleBasedIntentRouter, IntentLabel
from app.schemas.chat import ChatRequest


@pytest.mark.asyncio
async def test_all_four_departments_and_agents_registered(db_session):
    """Criteria 1: Verify all 4 departments and agents are registered correctly."""
    orchestrator = Orchestrator(db=db_session)
    assert "sales" in orchestrator.agents
    assert "hr" in orchestrator.agents
    assert "finance" in orchestrator.agents
    assert "operations" in orchestrator.agents
    assert isinstance(orchestrator.agents["sales"], SalesAgent)
    assert isinstance(orchestrator.agents["hr"], HRAgent)
    assert isinstance(orchestrator.agents["finance"], FinanceAgent)
    assert isinstance(orchestrator.agents["operations"], OperationsAgent)


@pytest.mark.asyncio
async def test_all_agents_use_same_shared_llm_client(db_session):
    """Criteria 2: All agents use the same configured shared Ollama model client."""
    shared_llm = get_shared_ollama_service()
    orchestrator = Orchestrator(db=db_session)

    assert orchestrator.ollama is shared_llm
    assert orchestrator.agents["sales"].llm is shared_llm
    assert orchestrator.agents["hr"].llm is shared_llm
    assert orchestrator.agents["finance"].llm is shared_llm
    assert orchestrator.agents["operations"].llm is shared_llm
    assert shared_llm.model_name == "qwen3:8b"


@pytest.mark.asyncio
async def test_router_classifies_all_four_departments():
    """Verify RuleBasedIntentRouter recognizes all 4 departments."""
    router = RuleBasedIntentRouter()

    res_sales = router.classify_intent("Tell me about our sales pipeline deals")
    assert res_sales.intent == IntentLabel.SALES

    res_hr = router.classify_intent("How many days of sick leave are permitted?")
    assert res_hr.intent == IntentLabel.HR

    res_fin = router.classify_intent("Which invoices are currently overdue for payment?")
    assert res_fin.intent == IntentLabel.FINANCE

    res_ops = router.classify_intent("What is the warehouse inventory level for optical transceivers?")
    assert res_ops.intent == IntentLabel.OPERATIONS


@pytest.mark.asyncio
async def test_operations_agent_retrieval(db_session, admin_user):
    """Criteria 3: Operations agent retrieves authorized inventory items and docs."""
    agent = OperationsAgent(db=db_session)
    result = await agent.execute_task(
        user=admin_user,
        task_query="warehouse inventory stock for Cat6A",
        correlation_id="test-ops-cid"
    )
    assert result.success is True
    assert result.department == "operations"
    assert len(result.evidence) > 0
    assert any("operations" in ev.department.lower() for ev in result.evidence)


@pytest.mark.asyncio
async def test_agent_disabled_state_blocks_execution(db_session, admin_user):
    """Verify an agent in disabled state refuses new chat queries."""
    from app.repositories.agent_repo import DepartmentAgentRepository

    agent_repo = DepartmentAgentRepository(db_session)
    await agent_repo.toggle_enabled("operations", is_enabled=False)
    await db_session.commit()

    try:
        orchestrator = Orchestrator(db=db_session)
        req = ChatRequest(message="What is the stock in warehouse?")
        resp = await orchestrator.handle_chat(admin_user, req)
        assert resp.error == "Agent disabled by administrator policy."
        assert "disabled by administrator policy" in resp.answer
    finally:
        # Re-enable for subsequent tests
        await agent_repo.toggle_enabled("operations", is_enabled=True)
        await db_session.commit()
