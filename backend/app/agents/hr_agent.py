from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent, AgentTaskResult
from app.db.models.user import User
from app.repositories.business_repo import HRRepository
from app.repositories.document_repo import DocumentChunkRepository
from app.repositories.audit_repo import AuditRepository
from app.permissions.policies import evaluate_policy, Role, ResourceType, Action
from app.services.ollama_service import get_shared_ollama_service
from app.schemas.chat import EvidenceReference


class HRAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("hr", db)
        self.hr_repo = HRRepository(db)
        self.doc_repo = DocumentChunkRepository(db)
        self.audit_repo = AuditRepository(db)
        self.llm = get_shared_ollama_service()


    async def execute_task(
        self,
        user: User,
        task_query: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentTaskResult:
        query_lower = task_query.lower()
        evidence_list: List[EvidenceReference] = []

        is_salary_query = any(w in query_lower for w in ["salary", "compensation", "payroll", "wage"])

        if is_salary_query:
            # Check policy specifically for sensitive salary data
            is_allowed, reason = evaluate_policy(
                user_role=user.role,
                user_department_code="hr",
                resource_department_code="hr",
                resource_type=ResourceType.SALARY.value,
                action=Action.READ.value,
                is_sensitive=True
            )

            if not is_allowed:
                await self.audit_repo.log_event(
                    action="hr_agent:salary_query_denied",
                    resource_type=ResourceType.SALARY.value,
                    outcome="deny",
                    reason=reason,
                    correlation_id=correlation_id,
                    actor_id=user.id,
                    actor_email=user.email,
                    actor_role=user.role,
                    actor_department="hr"
                )
                return AgentTaskResult(
                    success=False,
                    department=self.department_code,
                    content="Access Denied: Compensation and salary records are strictly restricted to HR Management.",
                    evidence=[],
                    error="Confidential salary data access denied."
                )

        # Authorized HR query: fetch employees and documents
        employees = await self.hr_repo.list_employees(
            department_id=user.department_id,
            include_sensitive=(user.role == Role.DEPARTMENT_MANAGER.value)
        )

        for emp in employees[:5]:
            snippet = f"Employee {emp.full_name} ({emp.employee_code}): Position: {emp.position}, Leave Balance: {emp.leave_balance} days."
            if is_salary_query and user.role == Role.DEPARTMENT_MANAGER.value:
                snippet += f" [Sensitive] Base Salary: ${emp.salary:,.2f}."
            evidence_list.append(EvidenceReference(
                source_type="business_record",
                title=f"HR Record: {emp.full_name}",
                department="hr",
                snippet=snippet
            ))

        # Search authorized HR documents
        terms = [t for t in query_lower.split() if len(t) > 3]
        doc_chunks = await self.doc_repo.search_chunks_by_keywords(
            query_terms=terms,
            department_id=user.department_id,
            allowed_access_levels=["public", "internal"]
        )
        for ch in doc_chunks:
            evidence_list.append(EvidenceReference(
                source_type="document",
                title="HR Policy Document",
                chunk_id=ch.id,
                department="hr",
                snippet=ch.content
            ))

        content = f"Retrieved {len(evidence_list)} authorized HR records and policy documents."
        return AgentTaskResult(
            success=True,
            department=self.department_code,
            content=content,
            evidence=evidence_list
        )
