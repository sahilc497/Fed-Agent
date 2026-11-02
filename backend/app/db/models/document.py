from typing import Optional, List, Any
import numpy as np
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    def __init__(
        self,
        id: Optional[int] = None,
        title: str = "",
        filename: str = "",
        file_path: str = "",
        file_type: str = "txt",
        department_id: int = 1,
        access_level: str = "internal",
        uploaded_by: int = 1,
        status: str = "indexed",
        created_at: Optional[str] = None,
        chunks: Optional[List[Any]] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            title=title,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            department_id=department_id,
            access_level=access_level,
            uploaded_by=uploaded_by,
            status=status,
            created_at=created_at,
            chunks=chunks or [],
            **kwargs
        )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    def __init__(
        self,
        id: Optional[int] = None,
        document_id: int = 1,
        chunk_index: int = 0,
        content: str = "",
        page_number: Optional[int] = None,
        department_id: int = 1,
        access_level: str = "internal",
        embedding: Optional[List[float]] = None,
        embedding_blob: Optional[bytes] = None,
        embedding_dimension: int = 384,
        created_at: Optional[str] = None,
        **kwargs
    ):
        blob = embedding_blob
        if embedding is not None and blob is None:
            arr = np.array(embedding, dtype=np.float32)
            blob = arr.tobytes()
            embedding_dimension = len(embedding)

        super().__init__(
            id=id,
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            page_number=page_number,
            department_id=department_id,
            access_level=access_level,
            embedding_blob=blob,
            embedding_dimension=embedding_dimension,
            created_at=created_at,
            **kwargs
        )

    @property
    def embedding(self) -> Optional[List[float]]:
        if getattr(self, "embedding_blob", None):
            arr = np.frombuffer(self.embedding_blob, dtype=np.float32)
            return arr.tolist()
        return None

    @embedding.setter
    def embedding(self, val: Optional[List[float]]):
        if val is not None:
            arr = np.array(val, dtype=np.float32)
            self.embedding_blob = arr.tobytes()
            self.embedding_dimension = len(val)
        else:
            self.embedding_blob = None
