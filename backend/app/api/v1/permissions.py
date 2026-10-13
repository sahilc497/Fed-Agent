from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.services.permission_service import PermissionService
from app.schemas.permission import PermissionCheckRequest, PermissionCheckResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/me")
async def get_my_permissions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Returns caller role, department context, and permission metadata."""
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "department_id": current_user.department_id,
        "policy_rule": "Strict department isolation with Federation Gateway for cross-department data"
    }


@router.post("/check", response_model=PermissionCheckResponse)
async def check_action_permission(
    data: PermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Evaluates whether an action is authorized under current policy matrix."""
    perm_service = PermissionService(db)
    is_allowed = await perm_service.check_permission(
        user=current_user,
        resource_type=data.resource_type,
        action=data.action,
        resource_department_code=data.resource_department,
        resource_id=data.resource_id,
        raise_on_denial=False
    )
    return PermissionCheckResponse(
        is_allowed=is_allowed,
        reason="Operation permitted by policy matrix" if is_allowed else "Operation denied by department policy matrix",
        policy_matched=f"Role:{current_user.role} on {data.resource_type}:{data.action}"
    )
