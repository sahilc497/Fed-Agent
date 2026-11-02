import datetime
from typing import Optional, Union
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    department_id: int
    role: str
    is_active: bool = True
    bio: Optional[str] = ""


class UserCreate(UserBase):
    password: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None


UserUpdate = UserProfileUpdate


class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    email: EmailStr
    full_name: str
    department_id: int
    role: str
    is_active: bool
    bio: Optional[str] = ""
    created_at: Optional[Union[datetime.datetime, str]] = None
