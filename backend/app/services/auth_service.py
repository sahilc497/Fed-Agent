from typing import Any, Optional
from app.core.security import verify_password, hash_password, create_access_token, decode_access_token
from app.core.exceptions import AuthenticationError
from app.db.models.user import User
from app.repositories.user_repo import UserRepository, DepartmentRepository
from app.schemas.auth import LoginRequest, Token, UserOut


class AuthService:
    def __init__(self, db: Any):
        self.db = db
        self.user_repo = UserRepository(db)
        self.dept_repo = DepartmentRepository(db)

    async def authenticate(self, credentials: LoginRequest) -> Token:
        user = await self.user_repo.get_by_email(credentials.email)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid email or password.")

        if not verify_password(credentials.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        dept = await self.dept_repo.get_by_id(user.department_id)
        dept_code = dept.code if dept else "unknown"

        token_claims = {
            "email": user.email,
            "role": user.role,
            "department_id": user.department_id,
            "department_code": dept_code
        }
        token_str = create_access_token(subject=user.id, claims=token_claims)

        user_out = UserOut.model_validate(user)
        return Token(
            access_token=token_str,
            token_type="bearer",
            expires_in_minutes=60,
            user=user_out
        )

    async def get_current_user(self, token_str: str) -> User:
        try:
            payload = decode_access_token(token_str)
            user_id = int(payload.get("sub"))
        except Exception as e:
            raise AuthenticationError("Invalid or expired authentication token.") from e

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User account inactive or not found.")
        return user
