import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DepartmentAgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    agent_code: str
    name: str
    description: str
    system_prompt: str
    is_enabled: bool
    error_count: int
    last_error: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class DepartmentAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_enabled: Optional[bool] = None
