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
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    answer: str
    intent: str  # sales, hr, finance, operations, multi_department, unknown
    routed_departments: List[str]
    evidence: List[EvidenceReference] = []
    is_incomplete_or_uncertain: bool = False
    approval_required: bool = False
    approval_id: Optional[str] = None
    error: Optional[str] = None
    correlation_id: str


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationOut(BaseModel):
    id: str
    user_id: int
    department_id: int
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatMessageOut(BaseModel):
    id: int
    conversation_id: str
    sender_role: str
    message: str
    content: Optional[str] = None
    intent: Optional[str] = None
    routed_departments: List[str] = []
    evidence_json: List[dict] = []
    created_at: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if self.content is None:
            self.content = self.message
