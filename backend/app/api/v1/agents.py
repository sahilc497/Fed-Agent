from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user
from app.services.agent_service import DepartmentAgentService
from app.schemas.agent import DepartmentAgentOut, DepartmentAgentUpdate
from app.core.exceptions import PermissionDeniedError, NotFoundError

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=List[DepartmentAgentOut])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Lists registered department agents and their enabled/disabled health status."""
    service = DepartmentAgentService(db)
    return await service.list_agents()


@router.get("/{agent_code}", response_model=DepartmentAgentOut)
async def get_agent(
    agent_code: str,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Retrieves an agent's configuration and status."""
    service = DepartmentAgentService(db)
    try:
        return await service.get_agent(agent_code)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{agent_code}", response_model=DepartmentAgentOut)
async def update_agent(
    agent_code: str,
    data: DepartmentAgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Administrator-only: updates agent configuration (prompt, name, status)."""
    service = DepartmentAgentService(db)
    try:
        return await service.update_agent(agent_code, current_user, data)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{agent_code}/toggle", response_model=DepartmentAgentOut)
async def toggle_agent(
    agent_code: str,
    is_enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Administrator-only: toggles department agent enabled or disabled state."""
    service = DepartmentAgentService(db)
    try:
        return await service.toggle_agent(agent_code, current_user, is_enabled)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
