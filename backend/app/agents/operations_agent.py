import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent, AgentTaskResult
from app.db.models.user import User
from app.gateway.service import FederationGatewayService
from app.repositories.business_repo import OperationsRepository
from app.repositories.document_repo import DocumentChunkRepository
from app.repositories.audit_repo import AuditRepository
from app.services.ollama_service import get_shared_ollama_service
from app.schemas.chat import EvidenceReference

logger = logging.getLogger("federated_mesh.agents.operations")


class OperationsAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("operations", db)
        self.ops_repo = OperationsRepository(db)
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

        # 1. Fetch authorized operations inventory items
        from app.repositories.user_repo import DepartmentRepository
        dept_repo = DepartmentRepository(self.db)
        ops_dept = await dept_repo.get_by_code("operations")
        dept_id = ops_dept.id if ops_dept else user.department_id
        items = await self.ops_repo.list_items(department_id=dept_id)


        # Keyword filtering on inventory items if query mentions specific terms
        matched_items = []
        for it in items:
            if any(term in it.item_name.lower() or term in it.sku.lower() or term in it.category.lower() or term in it.warehouse_location.lower() for term in query_lower.split() if len(term) > 3):
                matched_items.append(it)

        # If specific items matched, use them; otherwise use top 5 inventory items
        target_items = matched_items[:5] if matched_items else items[:5]
        for it in target_items:
            ev = EvidenceReference(
                source_type="business_record",
                title=f"Inventory: {it.item_name} ({it.sku})",
                department="operations",
                snippet=f"SKU: {it.sku}, Name: '{it.item_name}', Category: {it.category}, On Hand: {it.quantity_on_hand} units, Reorder Level: {it.reorder_threshold}, Location: {it.warehouse_location}, Status: {it.status}."
            )
            evidence_list.append(ev)

        # 2. Search authorized operations documents
        terms = [t for t in query_lower.split() if len(t) > 3]
        doc_chunks = await self.doc_repo.search_chunks_by_keywords(
            query_terms=terms,
            department_id=dept_id,
            allowed_access_levels=["public", "internal"]
        )
        for ch in doc_chunks:
            evidence_list.append(EvidenceReference(
                source_type="document",
                title="Operations Knowledge Document",
                chunk_id=ch.id,
                department="operations",
                snippet=ch.content
            ))

        content = f"Retrieved {len(evidence_list)} authorized Operations records and documents for query: {task_query}"
        return AgentTaskResult(
            success=True,
            department=self.department_code,
            content=content,
            evidence=evidence_list
        )
