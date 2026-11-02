import uuid
import datetime
import logging
from typing import List, Optional, Dict, Any
from app.core.exceptions import LLMServiceUnavailableError
from app.core.logging import get_correlation_id
from app.db.models.user import User
from app.orchestrator.router_interface import BaseIntentRouter, RuleBasedIntentRouter, IntentLabel
from app.orchestrator.ml_router import MLIntentRouter
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
from app.services.federation_service import parse_dt, STRICTLY_FORBIDDEN_FIELDS

logger = logging.getLogger("federated_mesh.orchestrator")


class Orchestrator:
    def __init__(
        self,
        db: Any,
        router: Optional[BaseIntentRouter] = None,
        ollama_service: Optional[OllamaService] = None
    ):
        self.db = db
        self.router = router or MLIntentRouter()
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

        # If intent is UNKNOWN but a valid department_hint is provided (e.g. from an active Cross-Department session),
        # route to that target department agent while strictly enforcing zero-trust grant checks
        if intent == IntentLabel.UNKNOWN and request.department_hint:
            hint_clean = request.department_hint.lower().strip()
            valid_hints = {
                "sales": IntentLabel.SALES,
                "hr": IntentLabel.HR,
                "finance": IntentLabel.FINANCE,
                "operations": IntentLabel.OPERATIONS,
            }
            if hint_clean in valid_hints:
                intent = valid_hints[hint_clean]
                logger.info(f"Adopted department_hint '{hint_clean}' for ambiguous query intent.")

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
        grant_notice: Optional[str] = None

        # 3. Multi-Department Handling
        if intent == IntentLabel.MULTI_DEPARTMENT:
            # Determine departments dynamically from route result explanation or default to sales/finance
            possible_depts = ["sales", "hr", "finance", "operations"]
            target_multi = [d for d in possible_depts if d in route_result.explanation.lower()]
            routed_depts = target_multi if target_multi else ["sales", "finance"]

            denied_depts = []
            for dept_code in routed_depts:
                # Check agent enabled status
                agent_rec = await self.agent_repo.get_by_code(dept_code)
                if agent_rec and not agent_rec.is_enabled:
                    continue

                # Cross-department check within multi-dept query
                if user.role != "admin" and user_dept_code != dept_code:
                    target_dept_obj = await self.dept_repo.get_by_code(dept_code)
                    active_grant = None
                    if target_dept_obj:
                        all_reqs = await self.fed_repo.list_requests(department_id=user.department_id, status="APPROVED")
                        now = datetime.datetime.now(datetime.timezone.utc)
                        active_grant = next(
                            (g for g in all_reqs if g.requester_user_id == user.id and g.source_department_id == target_dept_obj.id and parse_dt(g.expires_at) and parse_dt(g.expires_at) > now and g.revoked_at is None),
                            None
                        )
                    if not active_grant:
                        denied_depts.append(dept_code)
                        continue

                agent = self.agents.get(dept_code)
                if agent:
                    res = await agent.execute_task(user, request.message, cid)
                    if res.success:
                        collected_evidence.extend(res.evidence)

            # Zero-Trust enforcement: If non-admin user queried foreign departments without active grants
            if user.role != "admin" and denied_depts and not collected_evidence:
                denied_str = ", ".join([d.upper() for d in denied_depts])
                denial_msg = (
                    f"Access Denied: Cross-department direct access to {denied_str} records is restricted under Zero-Trust policy. "
                    f"Your access grant is either not yet approved, expired, or has been revoked by an administrator. "
                    f"Please submit an active Federation Access Request in the Approvals & Federation tab."
                )
                await self.audit_repo.log_event(
                    action="orchestrator:cross_dept_denial",
                    resource_type="multi_department_resource",
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
                target_dept_obj = await self.dept_repo.get_by_code(target_dept)
                user_requests = []
                if target_dept_obj:
                    all_reqs = await self.fed_repo.list_requests(department_id=user.department_id)
                    user_requests = [
                        r for r in all_reqs 
                        if r.requester_user_id == user.id and r.source_department_id == target_dept_obj.id
                    ]

                now = datetime.datetime.now(datetime.timezone.utc)
                # First check for an active approved grant
                active_grant = next(
                    (r for r in user_requests 
                     if r.status == "APPROVED" 
                     and r.revoked_at is None 
                     and (parse_dt(r.expires_at) is None or parse_dt(r.expires_at) > now)),
                    None
                )

                if active_grant:
                    # Authorized via Federation Access Request grant
                    target_agent = self.agents.get(target_dept)
                    if not target_agent:
                        return ChatResponse(
                            answer=f"Target agent for department {target_dept} is unavailable.",
                            intent=intent.value,
                            routed_departments=routed_depts,
                            is_incomplete_or_uncertain=True,
                            correlation_id=cid
                        )

                    res = await target_agent.execute_task(user, request.message, cid)

                    # Strictly sanitize forbidden fields from evidence
                    clean_evidence = []
                    for ev in res.evidence:
                        snippet_lower = ev.snippet.lower()
                        if any(f in snippet_lower for f in ["base salary:", "salary:", "payroll:", "bank_details"]):
                            continue
                        clean_evidence.append(ev)
                    res.evidence = clean_evidence

                    # Record grant usage timestamp (maintaining APPROVED state for repeated queries during time limit)
                    conn = getattr(self.db, "conn", self.db)
                    conn.execute(
                        "UPDATE federation_access_requests SET used_at = ? WHERE id = ?;",
                        (now.isoformat(), active_grant.id)
                    )

                    await self.audit_repo.log_event(
                        action="gateway:federated_request",
                        resource_type=f"cross_dept:{target_dept}",
                        outcome="allow",
                        reason=f"Federated cross-department access authorized via grant {active_grant.id}",
                        correlation_id=cid,
                        actor_id=user.id,
                        actor_email=user.email,
                        actor_role=user.role,
                        actor_department=user_dept_code,
                        resource_id=active_grant.id,
                        details={
                            "source_department": target_dept,
                            "grant_id": active_grant.id,
                            "expires_at": str(active_grant.expires_at),
                            "approved_fields": active_grant.approved_fields
                        }
                    )
                    await self.db.commit()

                    routed_depts = [user_dept_code, "gateway", target_dept]
                    grant_notice = f"[Federated Access via Approved Grant #{active_grant.id[:8]} - {target_dept.upper()} Scope]"
                else:
                    # Inspect the user's most recent request for this target department
                    latest_req = user_requests[0] if user_requests else None
                    if latest_req:
                        exp_dt = parse_dt(latest_req.expires_at)
                        is_expired = (exp_dt is not None and exp_dt < now)
                        is_revoked = (latest_req.status == "REVOKED" or latest_req.revoked_at is not None)

                        if latest_req.status == "PENDING":
                            if is_expired:
                                denial_msg = (
                                    f"Access Denied: Your Federation Access Request for {target_dept.upper()} department records "
                                    f"(Request #{latest_req.id[:8]}) has EXPIRED. The approved time limit has elapsed. "
                                    f"Please submit a new Federation Access Request in the Approvals & Federation tab."
                                )
                                err_type = "Federation grant expired."
                                action_name = "orchestrator:cross_dept_expired"
                            else:
                                denial_msg = (
                                    f"Access Denied: Your Federation Access Request for {target_dept.upper()} department records "
                                    f"(Request #{latest_req.id[:8]}) is currently pending Administrator approval. "
                                    f"Once approved, you will be able to query {target_dept.upper()} data here until the approved time limit expires."
                                )
                                err_type = "Federation request pending approval."
                                action_name = "orchestrator:cross_dept_pending"
                        elif is_revoked:
                            denial_msg = (
                                f"Access Denied: Your Federation Access Grant for {target_dept.upper()} department records "
                                f"(Request #{latest_req.id[:8]}) has been REVOKED by an Administrator. Direct access is prohibited."
                            )
                            err_type = "Federation grant revoked."
                            action_name = "orchestrator:cross_dept_revoked"
                        elif is_expired or latest_req.status == "EXPIRED":
                            denial_msg = (
                                f"Access Denied: Your Federation Access Grant for {target_dept.upper()} department records "
                                f"(Request #{latest_req.id[:8]}) has EXPIRED. The approved time limit has elapsed. "
                                f"Please submit a new Federation Access Request in the Approvals & Federation tab."
                            )
                            err_type = "Federation grant expired."
                            action_name = "orchestrator:cross_dept_expired"
                        elif latest_req.status == "REJECTED":
                            denial_msg = (
                                f"Access Denied: Your Federation Access Request for {target_dept.upper()} department records "
                                f"(Request #{latest_req.id[:8]}) was REJECTED by an Administrator. "
                                f"Reason: {latest_req.decision_reason or 'Policy denial'}."
                            )
                            err_type = "Federation request rejected."
                            action_name = "orchestrator:cross_dept_denial"
                        else:
                            denial_msg = (
                                f"Access Denied: Your Federation Access Grant for {target_dept.upper()} department records "
                                f"(Request #{latest_req.id[:8]}) has EXPIRED. The approved time limit has elapsed. "
                                f"Please submit a new Federation Access Request in the Approvals & Federation tab."
                            )
                            err_type = "Federation grant expired."
                            action_name = "orchestrator:cross_dept_expired"
                    else:
                        denial_msg = (
                            f"Access Denied: Cross-department direct access from {user_dept_code.upper()} to {target_dept.upper()} "
                            f"is prohibited. Please submit a Federation Access Request for administrator approval."
                        )
                        err_type = "Unauthorized cross-department access."
                        action_name = "orchestrator:cross_dept_denial"

                    await self.audit_repo.log_event(
                        action=action_name,
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
                        error=err_type,
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

        # If granted via active federation grant, prepend the grant notice badge
        if grant_notice:
            llm_answer = f"{grant_notice}\n\n{llm_answer}"

        # 7. Audit Request and Commit to SQLite
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
