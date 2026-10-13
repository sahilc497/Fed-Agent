from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def list_by_department(
        self,
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None
    ) -> List[Document]:
        allowed_levels = allowed_access_levels or ["public", "internal"]
        conditions = [Document.access_level.in_(allowed_levels)]
        if department_id is not None:
            conditions.append(Document.department_id == department_id)
        stmt = select(Document).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_authorized_document(
        self,
        document_id: int,
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None
    ) -> Optional[Document]:
        allowed_levels = allowed_access_levels or ["public", "internal"]
        conditions = [
            Document.id == document_id,
            Document.access_level.in_(allowed_levels)
        ]
        if department_id is not None:
            conditions.append(Document.department_id == department_id)
        stmt = select(Document).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    def __init__(self, db: AsyncSession):
        super().__init__(DocumentChunk, db)

    async def list_authorized_chunks(
        self,
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None
    ) -> List[DocumentChunk]:
        """Strict in-database authorization filtering."""
        allowed_levels = allowed_access_levels or ["public", "internal"]
        conditions = [DocumentChunk.access_level.in_(allowed_levels)]
        if department_id is not None:
            conditions.append(DocumentChunk.department_id == department_id)
        stmt = select(DocumentChunk).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_chunks_by_keywords(
        self,
        query_terms: List[str],
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[DocumentChunk]:
        """In-database search with strict department and access-level boundary enforcement."""
        allowed_levels = allowed_access_levels or ["public", "internal"]
        conditions = [DocumentChunk.access_level.in_(allowed_levels)]
        if department_id is not None:
            conditions.append(DocumentChunk.department_id == department_id)
        stmt = select(DocumentChunk).where(and_(*conditions))
        result = await self.db.execute(stmt)
        chunks = list(result.scalars().all())

        if not query_terms:
            return chunks[:limit]

        # Score matching keywords safely
        scored = []
        for ch in chunks:
            text = ch.content.lower()
            score = sum(1 for term in query_terms if term.lower() in text)
            if score > 0:
                scored.append((score, ch))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ch for _, ch in scored][:limit]
