from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user
from app.services.federation_service import FederationService
from app.schemas.federation import (
    FederationRequestCreate,
    FederationRequestDecision,
    FederationRequestOut,
    FederationConsumeResult
)
from app.core.exceptions import PermissionDeniedError, NotFoundError

router = APIRouter(prefix="/federation", tags=["Federation"])


@router.post("/requests", response_model=FederationRequestOut)
async def create_federation_request(
    data: FederationRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Submits a narrowly scoped Federation Access Request for cross-department data."""
    service = FederationService(db)
    try:
        return await service.create_request(current_user, data)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/requests", response_model=List[FederationRequestOut])
async def list_federation_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Lists federation access requests. Administrators view all; employees view departmental requests."""
    service = FederationService(db)
    return await service.list_requests(current_user, status=status_filter)


@router.get("/requests/{request_id}", response_model=FederationRequestOut)
async def get_federation_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Retrieves specific federation access request details."""
    service = FederationService(db)
    try:
        return await service.get_request(request_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/requests/{request_id}/decision", response_model=FederationRequestOut)
async def decide_federation_request(
    request_id: str,
    decision_data: FederationRequestDecision,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Administrator-only: approves or rejects a federation access request with mandatory reason.
    Self-approval is forbidden.
    """
    service = FederationService(db)
    try:
        return await service.decide_request(request_id, current_user, decision_data)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/requests/{request_id}/revoke", response_model=FederationRequestOut)
async def revoke_federation_request(
    request_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Administrator-only: immediately revokes an approved federation grant."""
    service = FederationService(db)
    try:
        return await service.revoke_request(request_id, current_user, reason=reason)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/requests/{request_id}/consume", response_model=FederationConsumeResult)
async def consume_federation_grant(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Consumes an approved federation grant via the Federation Gateway.
    Returns strictly authorized, filtered records from the source department.
    """
    service = FederationService(db)
    try:
        return await service.consume_request(request_id, current_user)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
