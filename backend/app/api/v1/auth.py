from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserOut
from app.api.deps import get_current_user
from app.core.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with Argon2id verified credentials and issue signed JWT."""
    auth_service = AuthService(db)
    try:
        token = await auth_service.authenticate(credentials)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns profile for current authenticated user."""
    return UserOut.model_validate(current_user)
