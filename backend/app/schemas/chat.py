import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    source_type: str  # document, business_record, gateway_federated
    title: str
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    page_number: Optional[int] = None
    department: str
    snippet: str
    confidence: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    correlation_id: Optional[str] = None
    department_hint: Optional[str] = None


class ChatResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    answer: str
    intent: str  # sales, hr, finance, operations, multi_department, unknown
    routed_departments: List[str]
    evidence: List[EvidenceReference] = []
    is_incomplete_or_uncertain: bool = False
    approval_required: bool = False
    approval_id: Optional[str] = None
    error: Optional[str] = None
    correlation_id: str
