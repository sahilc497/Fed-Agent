from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.services.approval_service import ApprovalService
from app.schemas.approval import ApprovalOut, ApprovalDecisionRequest
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError, NotFoundError

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalOut])
async def list_approvals(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists approval requests within user's department scope."""
    app_service = ApprovalService(db)
    return await app_service.list_approvals(user=current_user, status=status_filter)


@router.get("/{approval_id}", response_model=ApprovalOut)
async def get_approval(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves an approval request."""
    app_service = ApprovalService(db)
    try:
        return await app_service.get_approval(approval_id, current_user)
    except (NotFoundError, PermissionDeniedError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve_request(
    approval_id: str,
    req_body: ApprovalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approves a sensitive action request. Self-approval is rejected."""
    app_service = ApprovalService(db)
    try:
        return await app_service.decide_approval(
            approval_id=approval_id,
            approver=current_user,
            decision="approve",
            reason=req_body.reason
        )
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject_request(
    approval_id: str,
    req_body: ApprovalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rejects a sensitive action request."""
    app_service = ApprovalService(db)
    try:
        return await app_service.decide_approval(
            approval_id=approval_id,
            approver=current_user,
            decision="reject",
            reason=req_body.reason
        )
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{approval_id}/execute")
async def execute_request(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes an approved sensitive action with idempotency enforcement."""
    app_service = ApprovalService(db)
    try:
        result = await app_service.execute_approved_action(approval_id=approval_id, executor=current_user)
        return result
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
