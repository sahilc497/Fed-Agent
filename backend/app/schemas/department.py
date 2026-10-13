import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime


class DepartmentSummary(BaseModel):
    department_id: int
    department_name: str
    department_code: str
    user_count: int
    authorized_document_count: int
    metrics: Dict[str, int | float | str]
