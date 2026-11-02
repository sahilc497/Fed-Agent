import json
import uuid
from typing import Optional, List, Any
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    def __init__(
        self,
        id: Optional[str] = None,
        user_id: int = 1,
        department_id: int = 1,
        title: str = "New Conversation",
        created_at: Optional[Any] = None,
        updated_at: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            id=id or str(uuid.uuid4()),
            user_id=user_id,
            department_id=department_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs
        )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    def __init__(
        self,
        id: Optional[int] = None,
        conversation_id: str = "",
        sender_role: str = "user",
        message: str = "",
        intent: Optional[str] = None,
        routed_departments: Optional[Any] = None,
        evidence_json: Optional[Any] = None,
        created_at: Optional[Any] = None,
        **kwargs
    ):
        r_depts = routed_departments if isinstance(routed_departments, list) else (json.loads(routed_departments) if isinstance(routed_departments, str) else [])
        ev = evidence_json if isinstance(evidence_json, list) else (json.loads(evidence_json) if isinstance(evidence_json, str) else [])

        super().__init__(
            id=id,
            conversation_id=conversation_id,
            sender_role=sender_role,
            message=message,
            intent=intent,
            routed_departments=r_depts,
            evidence_json=ev,
            created_at=created_at,
            **kwargs
        )
