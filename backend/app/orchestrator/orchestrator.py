import uuid
import datetime
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import LLMServiceUnavailableError
from app.core.logging import get_correlation_id
from app.db.models.user import User
from app.orchestrator.router_interface import BaseIntentRouter, RuleBasedIntentRouter, IntentLabel
from app.agents.sales_agent import SalesAgent
from app.agents.hr_agent import HRAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.operations_agent import OperationsAgent
from app.services.ollama_service import OllamaService, get_shared_ollama_service
from app.services.approval_service import ApprovalService
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import DepartmentRepository
from app.repositories.agent_repo import DepartmentAgentRepository
from app.repositories.federation_repo import FederationRequestRepository
from app.schemas.chat import ChatRequest, ChatResponse, EvidenceReference
from app.schemas.approval import ApprovalCreate
from app.gateway.service import PERMITTED_POLICIES

logger = logging.getLogger("federated_mesh.orchestrator")


class Orchestrator:
    def __init__(
        self,
        db: AsyncSession,
        router: Optional[BaseIntentRouter] = None,
        ollama_service: Optional[OllamaService] = None
    ):
        self.db = db
        self.router = router or RuleBasedIntentRouter()
        self.ollama = ollama_service or get_shared_ollama_service()
        self.approval_service = ApprovalService(db)
        self.audit_repo = AuditRepository(db)
        self.dept_repo = DepartmentRepository(db)
        self.agent_repo = DepartmentAgentRepository(db)
        self.fed_repo = FederationRequestRepository(db)

        # 4 Department Agents Registry
        self.agents = {
            "sales": SalesAgent(db),
            "hr": HRAgent(db),
            "finance": FinanceAgent(db),
            "operations": OperationsAgent(db),
        }

    async def handle_chat(self, user: User, request: ChatRequest) -> ChatResponse:
        cid = request.correlation_id or get_correlation_id()
        user_dept = await self.dept_repo.get_by_id(user.department_id)
        user_dept_code = user_dept.code if user_dept else "unknown"

        # 1. Intent Classification
        route_result = self.router.classify_intent(request.message)
        intent = route_result.intent

        # 2. Handle Unknown / Ambiguous queries
        if intent == IntentLabel.UNKNOWN:
            msg = (
                "Your request could not be matched with high confidence to Sales, HR, Finance, or Operations. "
                "Could you please clarify your question or specify which department's records you wish to query?"
            )
            return ChatResponse(
                answer=msg,
                intent=intent.value,
                routed_departments=[],
                is_incomplete_or_uncertain=True,
                correlation_id=cid
            )

        routed_depts: List[str] = []
        collected_evidence: List[EvidenceReference] = []

        # 3. Multi-Department Handling
        if intent == IntentLabel.MULTI_DEPARTMENT:
            routed_depts = ["sales", "finance"]  # Primary multi-dept scenario
            for dept_code in routed_depts:
                # Check agent enabled status
                agent_rec = await self.agent_repo.get_by_code(dept_code)
                if agent_rec and not agent_rec.is_enabled:
                    continue

                agent = self.agents.get(dept_code)
                if agent:
                    res = await agent.execute_task(user, request.message, cid)
                    if res.success:
                        collected_evidence.extend(res.evidence)

        # 4. Single Department Handling (Sales, HR, Finance, Operations)
        elif intent in [IntentLabel.SALES, IntentLabel.HR, IntentLabel.FINANCE, IntentLabel.OPERATIONS]:
            target_dept = intent.value
            routed_depts = [target_dept]

            # Check if agent is enabled
            agent_rec = await self.agent_repo.get_by_code(target_dept)
            if agent_rec and not agent_rec.is_enabled:
                disabled_msg = f"Agent for department '{target_dept.upper()}' is currently disabled by administrator policy."
                return ChatResponse(
                    answer=disabled_msg,
                    intent=intent.value,
                    routed_departments=routed_depts,
                    error="Agent disabled by administrator policy.",
                    correlation_id=cid
                )

            # Cross-department security boundary check:
            if user.role != "admin" and user_dept_code != target_dept:
                # Check whether user has an active APPROVED Federation grant for target_dept
                target_dept_obj = await self.dept_repo.get_by_code(target_dept)
                fed_grants = []
                if target_dept_obj:
                    fed_grants = await self.fed_repo.list_requests(
                        department_id=user.department_id,
                        status="APPROVED"
                    )
                # Filter to active grants from this user for this target department
                now = datetime.datetime.now(datetime.timezone.utc)
                active_grant = next(
                    (g for g in fed_grants if g.requester_user_id == user.id and target_dept_obj and g.source_department_id == target_dept_obj.id and g.expires_at > now and g.revoked_at is None),
                    None
                )

                if active_grant:
                    # Authorized via Federation Access Request grant
                    own_agent = self.agents.get(user_dept_code)
                    if own_agent:
                        res = await own_agent.execute_task(user, request.message, cid)
                    else:
                        target_agent = self.agents.get(target_dept)
                        res = await target_agent.execute_task(user, request.message, cid)
                elif (user_dept_code, target_dept) in PERMITTED_POLICIES:
                    # Pre-authorized Gateway policy bridge (e.g. Sales checking Finance status of opportunity)
                    own_agent = self.agents.get(user_dept_code)
                    if own_agent:
                        res = await own_agent.execute_task(user, request.message, cid)
                    else:
                        denial_msg = f"Access Denied: Direct invocation of {target_dept} agent is restricted."
                        return ChatResponse(
                            answer=denial_msg,
                            intent=intent.value,
                            routed_departments=routed_depts,
                            error="Unauthorized agent invocation.",
                            correlation_id=cid
                        )
                else:
                    denial_msg = (
                        f"Access Denied: Cross-department direct access from {user_dept_code.upper()} to {target_dept.upper()} "
                        f"is prohibited. Please submit a Federation Access Request for administrator approval."
                    )
                    await self.audit_repo.log_event(
                        action="orchestrator:cross_dept_denial",
                        resource_type=f"{target_dept}_resource",
                        outcome="deny",
                        reason=denial_msg,
                        correlation_id=cid,
                        actor_id=user.id,
                        actor_email=user.email,
                        actor_role=user.role,
                        actor_department=user_dept_code
                    )
                    await self.db.commit()
                    return ChatResponse(
                        answer=denial_msg,
                        intent=intent.value,
                        routed_departments=routed_depts,
                        error="Unauthorized cross-department access.",
                        correlation_id=cid
                    )
            else:
                agent = self.agents.get(target_dept)
                if not agent:
                    return ChatResponse(
                        answer=f"Agent for department {target_dept} is unavailable.",
                        intent=intent.value,
                        routed_departments=routed_depts,
                        is_incomplete_or_uncertain=True,
                        correlation_id=cid
                    )
                res = await agent.execute_task(user, request.message, cid)

            # Check if approval is required
            if res.metadata.get("approval_required"):
                app_create = ApprovalCreate(
                    action_type=res.metadata.get("action_type", "sensitive_operation"),
                    target_resource=res.metadata.get("target_resource", target_dept),
                    requested_operation=res.metadata.get("requested_operation", "execute"),
                    payload={"query": request.message, "department": target_dept}
                )
                app_out = await self.approval_service.create_approval_request(user, app_create)
                await self.db.commit()
                return ChatResponse(
                    answer=f"This sensitive action requires human authorization. Approval request '{app_out.id}' has been registered.",
                    intent=intent.value,
                    routed_departments=routed_depts,
                    approval_required=True,
                    approval_id=app_out.id,
                    correlation_id=cid
                )

            if not res.success:
                return ChatResponse(
                    answer=res.content,
                    intent=intent.value,
                    routed_departments=routed_depts,
                    error=res.error,
                    correlation_id=cid
                )

            collected_evidence.extend(res.evidence)

        # 6. LLM Grounded Generation using local Ollama (qwen3:8b)
        evidence_dicts = [e.model_dump() for e in collected_evidence]
        try:
            llm_answer = await self.ollama.generate_grounded_answer(
                prompt=f"User Question: {request.message}",
                evidence=evidence_dicts
            )
        except LLMServiceUnavailableError as llm_err:
            logger.warning(f"Ollama unavailable, providing deterministic fallback answer: {llm_err}")
            if collected_evidence:
                summary_points = "\n".join([f"- {ev.snippet}" for ev in collected_evidence[:3]])
                llm_answer = f"Retrieved authorized enterprise evidence:\n{summary_points}\n\n(Local Ollama inference status: {str(llm_err)})"
            else:
                llm_answer = f"No authorized records or evidence found. (Local Ollama inference status: {str(llm_err)})"

        # 7. Audit Request and Commit to PostgreSQL
        await self.audit_repo.log_event(
            action="chat:completed",
            resource_type="chat_orchestration",
            outcome="allow",
            reason=f"Chat answered via intent {intent.value}",
            correlation_id=cid,
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role,
            actor_department=user_dept_code,
            details={"intent": intent.value, "evidence_count": len(collected_evidence)}
        )
        await self.db.commit()

        return ChatResponse(
            answer=llm_answer,
            intent=intent.value,
            routed_departments=routed_depts,
            evidence=collected_evidence,
            is_incomplete_or_uncertain=(len(collected_evidence) == 0),
            correlation_id=cid
        )
