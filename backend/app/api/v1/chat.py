from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db
from app.db.models.user import User
from app.orchestrator.orchestrator import Orchestrator
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationOut,
    ChatMessageOut
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Retrieves all persistent conversations owned by the authenticated user."""
    conv_repo = ConversationRepository(db)
    convs = await conv_repo.list_for_user(current_user.id)
    return [ConversationOut(
        id=c.id,
        user_id=c.user_id,
        department_id=c.department_id,
        title=c.title,
        created_at=str(c.created_at) if c.created_at else None,
        updated_at=str(c.updated_at) if c.updated_at else None
    ) for c in convs]


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Creates a new persistent conversation for the authenticated user."""
    conv_repo = ConversationRepository(db)
    title = data.title or "New Conversation"
    c = await conv_repo.create_conversation(current_user.id, current_user.department_id, title)
    return ConversationOut(
        id=c.id,
        user_id=c.user_id,
        department_id=c.department_id,
        title=c.title,
        created_at=str(c.created_at) if c.created_at else None,
        updated_at=str(c.updated_at) if c.updated_at else None
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessageOut])
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Retrieves messages for a conversation, strictly validating ownership."""
    conv_repo = ConversationRepository(db)
    conv = await conv_repo.get_for_user(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    messages = await conv_repo.get_messages(conversation_id, current_user.id)
    return [ChatMessageOut(
        id=m.id,
        conversation_id=m.conversation_id,
        sender_role=m.sender_role,
        message=m.message,
        content=m.message,
        intent=m.intent,
        routed_departments=m.routed_departments or [],
        evidence_json=m.evidence_json or [],
        created_at=str(m.created_at) if m.created_at else None
    ) for m in messages]


@router.delete("/conversations/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Deletes a conversation owned by the authenticated user."""
    conv_repo = ConversationRepository(db)
    deleted = await conv_repo.delete_conversation(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {"message": "Conversation deleted successfully."}


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """
    Central Orchestrator endpoint:
    Classifies intent via locally trained ML Intent Router, enforces department boundaries,
    invokes agents, grounds answers in authorized evidence, and persists chat history to SQLite.
    """
    conv_repo = ConversationRepository(db)
    conv_id = request.conversation_id

    # Validate or create conversation for persistent history
    if conv_id:
        conv = await conv_repo.get_for_user(conv_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified conversation not found.")
    else:
        # Generate initial title from first 40 characters of message
        title_snippet = request.message[:40] + ("..." if len(request.message) > 40 else "")
        conv = await conv_repo.create_conversation(current_user.id, current_user.department_id, title_snippet)
        conv_id = conv.id

    # 1. Record incoming user message
    await conv_repo.add_message(
        conversation_id=conv_id,
        sender_role="user",
        message=request.message
    )

    # 2. Invoke Central Orchestrator
    orchestrator = Orchestrator(db)
    response = await orchestrator.handle_chat(current_user, request)
    response.conversation_id = conv_id

    # 3. Record assistant response with evidence and routed intent
    evidence_dicts = [e.model_dump() for e in response.evidence] if response.evidence else []
    await conv_repo.add_message(
        conversation_id=conv_id,
        sender_role="assistant",
        message=response.answer,
        intent=response.intent,
        routed_departments=response.routed_departments,
        evidence_json=evidence_dicts
    )

    return response
