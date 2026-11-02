from typing import Any, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.db.session import get_db, SqliteSession
from app.db.models.user import User
from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Any = Depends(get_db)
) -> User:
    """Dependency to retrieve and validate the authenticated user from the Bearer token."""
    auth_service = AuthService(db)
    try:
        user = await auth_service.get_current_user(token)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
