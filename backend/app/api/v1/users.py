from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db
from app.db.models.user import User
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserOut, UserProfileUpdate, UserAdminUpdate
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return UserOut.model_validate(current_user)


@router.put("/me", response_model=UserOut)
async def update_own_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Permits any employee or manager to edit their own permitted profile fields (full_name, bio)."""
    user_repo = UserRepository(db)
    updated = await user_repo.update_profile(
        user_id=current_user.id,
        full_name=data.full_name,
        bio=data.bio
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserOut.model_validate(updated)


@router.get("", response_model=List[UserOut])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Admin and Department Manager endpoint to list registered enterprise users."""
    if current_user.role not in ["admin", "department_manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Insufficient administrative privileges.")
    user_repo = UserRepository(db)
    if current_user.role == "admin":
        users = await user_repo.list_all()
    else:
        users = await user_repo.get_by_department(current_user.department_id)
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Admin-only endpoint to provision users."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can provision new users.")
    user_service = UserService(db)
    try:
        new_user = await user_service.create_user(creator=current_user, data=data)
        return new_user
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_id}", response_model=UserOut)
async def admin_update_user(
    user_id: int,
    data: UserAdminUpdate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Admin-only endpoint to update an employee's role, department, or active status."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can modify employee roles and department assignments.")
    user_repo = UserRepository(db)
    updated = await user_repo.update_admin(
        user_id=user_id,
        role=data.role,
        department_id=data.department_id,
        is_active=data.is_active,
        full_name=data.full_name
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserOut.model_validate(updated)


@router.delete("/{user_id}", response_model=dict)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Admin-only endpoint to safely deactivate an employee account (prevents historical deletion)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can deactivate accounts.")
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Administrators cannot deactivate their own active account.")
    user_repo = UserRepository(db)
    await user_repo.update_admin(user_id=user_id, is_active=False)
    return {"message": f"User {user_id} has been deactivated successfully.", "status": "deactivated"}
