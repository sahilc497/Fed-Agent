from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.document import DocumentChunk
from app.repositories.document_repo import DocumentChunkRepository
from app.rag.embeddings import get_embedding_service, compute_cosine_similarity
from app.schemas.chat import EvidenceReference


class RAGRetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunk_repo = DocumentChunkRepository(db)
        self.embedder = get_embedding_service()

    async def retrieve_evidence(
        self,
        query: str,
        department_id: int,
        department_code: str,
        allowed_access_levels: Optional[List[str]] = None,
        top_k: int = 4,
        similarity_threshold: float = 0.15
    ) -> List[EvidenceReference]:
        """
        Retrieves evidence strictly filtered to the user's department and access levels.
        No cross-department chunk leakage can occur at this layer.
        """
        levels = allowed_access_levels or ["public", "internal"]
        query_vec = self.embedder.embed_text(query)

        # 1. Fetch authorized chunks directly from DB
        authorized_chunks = await self.chunk_repo.list_authorized_chunks(
            department_id=department_id,
            allowed_access_levels=levels
        )

        if not authorized_chunks:
            return []

        # 2. Compute cosine similarity against pre-filtered chunks
        scored_chunks = []
        for ch in authorized_chunks:
            if ch.embedding:
                score = compute_cosine_similarity(query_vec, ch.embedding)
            else:
                score = 0.0

            if score >= similarity_threshold:
                scored_chunks.append((score, ch))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # 3. Format structured EvidenceReference objects
        evidence_list: List[EvidenceReference] = []
        for score, ch in scored_chunks[:top_k]:
            evidence_list.append(EvidenceReference(
                source_type="document",
                title=f"Internal Knowledge Doc #{ch.document_id}",
                document_id=ch.document_id,
                chunk_id=ch.id,
                page_number=ch.page_number,
                department=department_code,
                snippet=ch.content,
                confidence=round(score, 3)
            ))

        return evidence_list
