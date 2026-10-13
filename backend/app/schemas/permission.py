from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class PermissionCheckRequest(BaseModel):
    resource_type: str
    action: str
    resource_department: Optional[str] = None
    resource_id: Optional[str] = None
    purpose: Optional[str] = None


class PermissionCheckResponse(BaseModel):
    is_allowed: bool
    reason: str
    policy_matched: Optional[str] = None


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    department_id: Optional[int]
    resource_type: str
    action: str
    is_allowed: bool
    conditions: Dict[str, Any]
