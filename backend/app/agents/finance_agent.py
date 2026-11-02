from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgent, AgentTaskResult
from app.db.models.user import User
from app.repositories.business_repo import FinanceRepository
from app.repositories.document_repo import DocumentChunkRepository
from app.repositories.audit_repo import AuditRepository
from app.services.ollama_service import get_shared_ollama_service
from app.schemas.chat import EvidenceReference


class FinanceAgent(BaseAgent):
    def __init__(self, db: Any):
        super().__init__("finance", db)
        self.finance_repo = FinanceRepository(db)
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

        # Check for sensitive action requiring human approval (e.g. "pay invoice", "execute payment", "wire transfer")
        if any(w in query_lower for w in ["pay invoice", "execute payment", "make payment", "wire transfer", "send money"]):
            return AgentTaskResult(
                success=True,
                department=self.department_code,
                content="Sensitive financial operation detected. A human approval request is required before any payment execution.",
                evidence=[],
                metadata={
                    "approval_required": True,
                    "action_type": "payment_execution",
                    "target_resource": "finance_invoice",
                    "requested_operation": "execute_wire_payment"
                }
            )

        from app.repositories.user_repo import DepartmentRepository
        dept_repo = DepartmentRepository(self.db)
        fin_dept = await dept_repo.get_by_code("finance")
        dept_id = fin_dept.id if fin_dept else 3

        # Overdue invoice query
        if "overdue" in query_lower:
            invoices = await self.finance_repo.list_overdue_invoices(department_id=dept_id)
        else:
            invoices = await self.finance_repo.list_invoices(department_id=dept_id)

        # Match specific invoices if query mentions invoice numbers or client names
        matched_invs = [
            inv for inv in invoices
            if any(term in inv.invoice_number.lower() or term in inv.client_name.lower()
                   for term in query_lower.split() if len(term) > 2 and term not in ["the", "and", "for", "with", "from", "invoice", "invoices", "status", "show", "what"])
        ]
        target_invoices = matched_invs[:5] if matched_invs else invoices[:5]

        for inv in target_invoices:
            due_str = inv.due_date[:10] if isinstance(inv.due_date, str) else (inv.due_date.strftime('%Y-%m-%d') if hasattr(inv.due_date, 'strftime') else str(inv.due_date))
            evidence_list.append(EvidenceReference(
                source_type="business_record",
                title=f"Invoice {inv.invoice_number}",
                department="finance",
                snippet=f"Invoice {inv.invoice_number} for client '{inv.client_name}': Amount ${inv.amount:,.2f}, Status: {inv.status}, Due: {due_str}."
            ))

        # Search authorized finance documents
        terms = [t for t in query_lower.split() if len(t) > 3]
        doc_chunks = await self.doc_repo.search_chunks_by_keywords(
            query_terms=terms,
            department_id=dept_id,
            allowed_access_levels=["public", "internal"]
        )
        for ch in doc_chunks:
            evidence_list.append(EvidenceReference(
                source_type="document",
                title="Finance Guidelines Document",
                chunk_id=ch.id,
                department="finance",
                snippet=ch.content
            ))

        content = f"Retrieved {len(evidence_list)} authorized Finance records and invoices."
        return AgentTaskResult(
            success=True,
            department=self.department_code,
            content=content,
            evidence=evidence_list
        )
