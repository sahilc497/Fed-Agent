import numpy as np
from typing import List, Optional, Any
from app.db.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: Any):
        super().__init__(Document, db)

    async def list_by_department(
        self,
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None
    ) -> List[Document]:
        conn = self._get_conn()
        allowed_levels = allowed_access_levels or ["public", "internal"]
        placeholders = ",".join("?" for _ in allowed_levels)
        query = f"SELECT * FROM documents WHERE access_level IN ({placeholders})"
        params = list(allowed_levels)
        if department_id is not None:
            query += " AND department_id = ?"
            params.append(department_id)
        query += " ORDER BY id;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [Document.from_row(r) for r in rows]

    async def get_authorized_document(
        self,
        document_id: int,
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None
    ) -> Optional[Document]:
        conn = self._get_conn()
        allowed_levels = allowed_access_levels or ["public", "internal"]
        placeholders = ",".join("?" for _ in allowed_levels)
        query = f"SELECT * FROM documents WHERE id = ? AND access_level IN ({placeholders})"
        params = [document_id] + list(allowed_levels)
        if department_id is not None:
            query += " AND department_id = ?"
            params.append(department_id)
        cursor = conn.execute(query, tuple(params))
        row = cursor.fetchone()
        return Document.from_row(row) if row else None

    async def delete_document(self, document_id: int) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?;", (document_id,))
        conn.execute("DELETE FROM documents WHERE id = ?;", (document_id,))
        return True


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    def __init__(self, db: Any):
        super().__init__(DocumentChunk, db)

    async def list_authorized_chunks(
        self,
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None
    ) -> List[DocumentChunk]:
        """Strict in-database authorization filtering."""
        conn = self._get_conn()
        allowed_levels = allowed_access_levels or ["public", "internal"]
        placeholders = ",".join("?" for _ in allowed_levels)
        query = f"SELECT * FROM document_chunks WHERE access_level IN ({placeholders})"
        params = list(allowed_levels)
        if department_id is not None:
            query += " AND department_id = ?"
            params.append(department_id)
        query += " ORDER BY id;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [DocumentChunk.from_row(r) for r in rows]

    async def search_chunks_by_keywords(
        self,
        query_terms: List[str],
        department_id: Optional[int] = None,
        allowed_access_levels: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[DocumentChunk]:
        """In-database search with strict department and access-level boundary enforcement."""
        chunks = await self.list_authorized_chunks(department_id, allowed_access_levels)
        if not query_terms:
            return chunks[:limit]

        scored = []
        for ch in chunks:
            text = ch.content.lower()
            score = sum(1 for term in query_terms if term.lower() in text)
            if score > 0:
                scored.append((score, ch))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ch for _, ch in scored][:limit]

    async def save_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        department_id: int,
        access_level: str = "internal",
        page_number: Optional[int] = None,
        embedding: Optional[List[float]] = None
    ) -> DocumentChunk:
        conn = self._get_conn()
        blob = None
        dim = 384
        if embedding is not None:
            arr = np.array(embedding, dtype=np.float32)
            blob = arr.tobytes()
            dim = len(embedding)

        cursor = conn.execute(
            """INSERT INTO document_chunks (
                document_id, chunk_index, content, page_number,
                department_id, access_level, embedding_blob, embedding_dimension
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
            (document_id, chunk_index, content, page_number, department_id, access_level, blob, dim)
        )
        return DocumentChunk(
            id=cursor.lastrowid,
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            page_number=page_number,
            department_id=department_id,
            access_level=access_level,
            embedding_blob=blob,
            embedding_dimension=dim
        )
