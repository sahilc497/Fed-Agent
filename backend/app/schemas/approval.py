import datetime
from typing import Any, Dict, Optional, Union
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
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    requester_id: int
    requester_department_id: int
    action_type: str
    target_resource: str
    requested_operation: str
    payload: Dict[str, Any]
    status: str
    approver_id: Optional[int] = None
    idempotency_key: str
    created_at: Optional[Union[datetime.datetime, str]] = None
    decided_at: Optional[Union[datetime.datetime, str]] = None
    expires_at: Optional[Union[datetime.datetime, str]] = None
    executed_at: Optional[Union[datetime.datetime, str]] = None
    execution_result: Optional[Dict[str, Any]] = None
