from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: "UserOut"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    role: str
    department_id: int
    department_code: str


from app.schemas.user import UserOut  # noqa: E402
Token.model_rebuild()
