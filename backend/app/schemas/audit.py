import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: Optional[int]
    actor_email: Optional[str]
    actor_role: str
    actor_department: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    outcome: str
    reason: str
    correlation_id: str
    gateway_decision: Optional[Dict[str, Any]]
    details: Optional[Dict[str, Any]]
    timestamp: datetime.datetime


class AuditFilterParams(BaseModel):
    department: Optional[str] = None
    action: Optional[str] = None
    outcome: Optional[str] = None
    limit: int = 100
    offset: int = 0
