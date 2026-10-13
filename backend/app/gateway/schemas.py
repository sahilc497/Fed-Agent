import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FederationRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requesting_agent: str
    requesting_user_id: int
    requesting_department: str
    target_department: str
    business_purpose: str
    requested_fields: List[str]
    resource_identifiers: Optional[List[str]] = None
    requested_operation: str = "read_status"
    correlation_id: str


class FederationResponse(BaseModel):
    request_id: str
    is_allowed: bool
    status_code: int
    policy_reason: str
    filtered_data: Optional[List[Dict[str, Any]]] = None
    denied_fields: List[str] = []
    correlation_id: str
