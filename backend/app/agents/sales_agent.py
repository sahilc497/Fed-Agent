from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgent, AgentTaskResult
from app.db.models.user import User
from app.gateway.service import FederationGatewayService
from app.gateway.schemas import FederationRequest
from app.repositories.business_repo import SalesRepository
from app.repositories.document_repo import DocumentChunkRepository
from app.repositories.audit_repo import AuditRepository
from app.services.ollama_service import get_shared_ollama_service
from app.schemas.chat import EvidenceReference


class SalesAgent(BaseAgent):
    def __init__(self, db: Any):
        super().__init__("sales", db)
        self.sales_repo = SalesRepository(db)
        self.doc_repo = DocumentChunkRepository(db)
        self.audit_repo = AuditRepository(db)
        self.gateway = FederationGatewayService(db)
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

        # Check for cross-department request to Finance (e.g., opportunities awaiting finance approval)
        if "finance approval" in query_lower or "awaiting finance" in query_lower or "finance status" in query_lower:
            fed_req = FederationRequest(
                requesting_agent="sales_agent",
                requesting_user_id=user.id,
                requesting_department="sales",
                target_department="finance",
                business_purpose="opportunity_finance_status",
                requested_fields=["opportunity_id", "finance_status", "status"],
                correlation_id=correlation_id
            )
            fed_resp = await self.gateway.execute_federated_request(user, fed_req)

            if not fed_resp.is_allowed:
                return AgentTaskResult(
                    success=False,
                    department=self.department_code,
                    content=f"Gateway denied cross-department request: {fed_resp.policy_reason}",
                    evidence=[],
                    error=fed_resp.policy_reason
                )

            # Also fetch local sales opportunities needing finance approval
            opps = await self.sales_repo.list_awaiting_finance_approval(
                department_id=user.department_id if user.role != "admin" else None
            )
            for op in opps:
                ev = EvidenceReference(
                    source_type="business_record",
                    title=f"Opportunity {op.title}",
                    department="sales",
                    snippet=f"Opportunity '{op.title}' (Client: {op.client_name}, Value: ${op.deal_value:,.2f}) has finance status '{op.finance_status}'."
                )
                evidence_list.append(ev)

            content = f"Found {len(opps)} sales opportunities pending Finance review. Details retrieved through Federation Gateway."
            return AgentTaskResult(
                success=True,
                department=self.department_code,
                content=content,
                evidence=evidence_list
            )

        # Standard Sales query: fetch opportunities and authorized sales documents
        from app.repositories.user_repo import DepartmentRepository
        dept_repo = DepartmentRepository(self.db)
        sales_dept = await dept_repo.get_by_code("sales")
        dept_id = sales_dept.id if sales_dept else 1

        opps = await self.sales_repo.list_for_department(dept_id)
        # Match specific opportunities if query mentions deal titles or client names
        matched_opps = [
            op for op in opps
            if any(term in op.title.lower() or term in op.client_name.lower() or term in op.stage.lower()
                   for term in query_lower.split() if len(term) > 2 and term not in ["the", "and", "for", "with", "from", "deal", "deals", "show", "what"])
        ]
        target_opps = matched_opps[:5] if matched_opps else opps[:5]

        for op in target_opps:
            ev = EvidenceReference(
                source_type="business_record",
                title=f"Opportunity: {op.title}",
                department="sales",
                snippet=f"Client: {op.client_name}, Deal Value: ${op.deal_value:,.2f}, Stage: {op.stage}."
            )
            evidence_list.append(ev)

        # In-database search for sales documents
        terms = [t for t in query_lower.split() if len(t) > 3]
        doc_chunks = await self.doc_repo.search_chunks_by_keywords(
            query_terms=terms,
            department_id=dept_id,
            allowed_access_levels=["public", "internal"]
        )
        for ch in doc_chunks:
            evidence_list.append(EvidenceReference(
                source_type="document",
                title="Sales Knowledge Document",
                chunk_id=ch.id,
                department="sales",
                snippet=ch.content
            ))

        content = f"Retrieved {len(evidence_list)} authorized Sales records and documents for query: {task_query}"
        return AgentTaskResult(
            success=True,
            department=self.department_code,
            content=content,
            evidence=evidence_list
        )
