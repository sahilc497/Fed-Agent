from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserOut
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return UserOut.model_validate(current_user)


@router.get("", response_model=list[UserOut])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin and Auditor endpoint to list registered enterprise users."""
    if current_user.role not in ["admin", "auditor", "department_manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Insufficient administrative privileges.")
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository(db)
    users = await user_repo.list_all()
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only endpoint to provision users."""
    user_service = UserService(db)
    try:
        new_user = await user_service.create_user(creator=current_user, data=data)
        return new_user
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
