import os
import io
import re
from typing import List, Tuple, Any
from pypdf import PdfReader
from docx import Document as DocxDocument
from app.core.config import settings
from app.core.exceptions import DocumentProcessingError
from app.db.models.document import Document, DocumentChunk
from app.repositories.document_repo import DocumentRepository, DocumentChunkRepository
from app.rag.chunking import chunk_text
from app.rag.embeddings import get_embedding_service


class DocumentIngestionService:
    def __init__(self, db: Any):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        self.embedder = get_embedding_service()

    def sanitize_text(self, text: str) -> str:
        """Sanitizes document text to prevent control character injection."""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()

    def extract_text(self, file_bytes: bytes, file_type: str) -> List[Tuple[int, str]]:
        """
        Extracts text from file bytes with page numbers.
        Returns list of (page_number, text_content).
        """
        results: List[Tuple[int, str]] = []
        try:
            if file_type == "pdf":
                reader = PdfReader(io.BytesIO(file_bytes))
                for i, page in enumerate(reader.pages):
                    t = page.extract_text() or ""
                    clean_t = self.sanitize_text(t)
                    if clean_t:
                        results.append((i + 1, clean_t))
            elif file_type == "docx":
                doc = DocxDocument(io.BytesIO(file_bytes))
                full_text = []
                for p in doc.paragraphs:
                    if p.text:
                        full_text.append(p.text)
                clean_t = self.sanitize_text("\n".join(full_text))
                if clean_t:
                    results.append((1, clean_t))
            elif file_type == "txt":
                text = file_bytes.decode("utf-8", errors="replace")
                clean_t = self.sanitize_text(text)
                if clean_t:
                    results.append((1, clean_t))
            else:
                raise DocumentProcessingError(f"Unsupported file type: {file_type}")
        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise
            raise DocumentProcessingError(f"Failed to extract text from {file_type}: {str(e)}") from e

        return results

    async def ingest_document(
        self,
        title: str,
        filename: str,
        file_bytes: bytes,
        file_type: str,
        department_id: int,
        access_level: str,
        uploaded_by_id: int
    ) -> Document:
        """Ingests, chunks, embeds, and stores a document into SQLite."""
        # 1. Size check
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise DocumentProcessingError(f"File size ({size_mb:.2f}MB) exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

        # 2. Extension validation
        ext = file_type.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise DocumentProcessingError(f"Extension '{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")

        # 3. Create document record
        doc = Document(
            title=title,
            filename=filename,
            file_path=f"data/knowledge_base/{filename}",
            file_type=ext,
            department_id=department_id,
            access_level=access_level,
            uploaded_by=uploaded_by_id,
            status="processing"
        )
        created_doc = await self.doc_repo.create(doc)

        # 4. Extract text per page
        pages = self.extract_text(file_bytes, ext)
        if not pages:
            created_doc.status = "empty"
            return created_doc

        # 5. Chunk and embed locally
        global_chunk_idx = 0
        for page_num, page_content in pages:
            chunks = chunk_text(page_content, chunk_size=300, chunk_overlap=30, page_number=page_num)
            for c in chunks:
                vec = self.embedder.embed_text(c["content"])
                await self.chunk_repo.save_chunk(
                    document_id=created_doc.id,
                    chunk_index=global_chunk_idx,
                    content=c["content"],
                    department_id=department_id,
                    access_level=access_level,
                    page_number=page_num,
                    embedding=vec
                )
                global_chunk_idx += 1

        created_doc.status = "indexed"
        return created_doc
