from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.repositories.document_repo import DocumentRepository
from app.rag.ingestion import DocumentIngestionService
from app.schemas.document import DocumentOut
from app.api.deps import get_current_user
from app.core.exceptions import DocumentProcessingError

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    access_level: str = Form("internal"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploads, validates, chunks, embeds, and stores an internal document."""
    if access_level in ["confidential", "restricted"] and current_user.role not in ["admin", "department_manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot upload confidential documents as employee.")

    filename = file.filename or "uploaded_file.txt"
    file_ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    doc_title = title or filename

    content_bytes = await file.read()
    ingest_svc = DocumentIngestionService(db)

    try:
        doc = await ingest_svc.ingest_document(
            title=doc_title,
            filename=filename,
            file_bytes=content_bytes,
            file_type=file_ext,
            department_id=current_user.department_id,
            access_level=access_level,
            uploaded_by_id=current_user.id
        )
        return DocumentOut.model_validate(doc)
    except DocumentProcessingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DocumentOut])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists documents accessible to current user within their department."""
    doc_repo = DocumentRepository(db)
    allowed_levels = ["public", "internal"]
    if current_user.role in ["admin", "department_manager"]:
        allowed_levels.extend(["confidential", "restricted"])

    dept_filter = None if current_user.role == "admin" else current_user.department_id
    docs = await doc_repo.list_by_department(
        department_id=dept_filter,
        allowed_access_levels=allowed_levels
    )
    return [DocumentOut.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves document metadata if authorized."""
    doc_repo = DocumentRepository(db)
    allowed_levels = ["public", "internal"]
    if current_user.role in ["admin", "department_manager"]:
        allowed_levels.extend(["confidential", "restricted"])

    dept_filter = None if current_user.role == "admin" else current_user.department_id
    doc = await doc_repo.get_authorized_document(
        document_id=document_id,
        department_id=dept_filter,
        allowed_access_levels=allowed_levels
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or access denied.")
    return DocumentOut.model_validate(doc)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a document if caller is manager or administrator."""
    if current_user.role not in ["admin", "department_manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Managers or Admins can delete documents.")

    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get_by_id(document_id)
    if not doc or (current_user.role != "admin" and doc.department_id != current_user.department_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or access denied.")

    await db.delete(doc)
    return {"status": "deleted", "document_id": document_id}
