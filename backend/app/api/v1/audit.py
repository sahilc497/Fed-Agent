from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.db.session import get_db
from app.db.models.user import User
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogOut, AuditFilterParams
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=List[AuditLogOut])
async def list_audit_logs(
    department: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Retrieves audit logs.
    Restricted to Admins and Department Managers (scoped to department).
    """
    audit_service = AuditService(db)
    params = AuditFilterParams(
        department=department,
        action=action,
        outcome=outcome,
        limit=limit,
        offset=offset
    )
    try:
        return await audit_service.get_audit_logs(current_user, params)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
