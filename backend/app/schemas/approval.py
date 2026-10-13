import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class ApprovalCreate(BaseModel):
    action_type: str
    target_resource: str
    requested_operation: str
    payload: Dict[str, Any]
    idempotency_key: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: str  # approve, reject
    reason: Optional[str] = None


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requester_id: int
    requester_department_id: int
    action_type: str
    target_resource: str
    requested_operation: str
    payload: Dict[str, Any]
    status: str
    approver_id: Optional[int]
    idempotency_key: str
    created_at: datetime.datetime
    decided_at: Optional[datetime.datetime]
    expires_at: datetime.datetime
    executed_at: Optional[datetime.datetime]
    execution_result: Optional[Dict[str, Any]]
