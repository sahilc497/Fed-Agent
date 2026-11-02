import datetime
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class FederationRequestCreate(BaseModel):
    source_department_code: str = Field(..., description="Target department code: sales, hr, finance, or operations")
    business_purpose: str = Field(..., min_length=3, max_length=255)
    requested_fields: List[str] = Field(..., min_length=1)
    record_identifiers: Optional[List[str]] = Field(default_factory=list)
    access_duration_minutes: Optional[int] = Field(default=60, ge=5, le=1440)
    idempotency_key: Optional[str] = None


class FederationRequestDecision(BaseModel):
    decision: str = Field(..., description="approve or reject")
    reason: Optional[str] = Field(default=None, max_length=1000)
    approved_fields: Optional[List[str]] = None
    approved_record_ids: Optional[List[str]] = None


class FederationRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    requester_user_id: int
    requester_department_id: int
    requesting_agent: str
    source_department_id: int
    business_purpose: str
    requested_fields: List[str]
    record_identifiers: List[str]
    access_duration_minutes: int
    status: str
    approver_user_id: Optional[int] = None
    decision_reason: Optional[str] = None
    approved_fields: Optional[List[str]] = None
    approved_record_ids: Optional[List[str]] = None
    idempotency_key: str
    created_at: Optional[Union[datetime.datetime, str]] = None
    decided_at: Optional[Union[datetime.datetime, str]] = None
    expires_at: Optional[Union[datetime.datetime, str]] = None
    revoked_at: Optional[Union[datetime.datetime, str]] = None
    used_at: Optional[Union[datetime.datetime, str]] = None
    requester_email: Optional[str] = None
    source_department_code: Optional[str] = None
    requester_department_code: Optional[str] = None


class FederationConsumeResult(BaseModel):
    request_id: str
    status: str
    source_department: str
    released_fields: List[str]
    record_count: int
    records: List[dict]
