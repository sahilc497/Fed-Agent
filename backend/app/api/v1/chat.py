from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.orchestrator.orchestrator import Orchestrator
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Central Orchestrator endpoint:
    Classifies intent, enforces department boundaries, invokes agents, and generates evidence-grounded answers.
    """
    orchestrator = Orchestrator(db)
    response = await orchestrator.handle_chat(current_user, request)
    return response
