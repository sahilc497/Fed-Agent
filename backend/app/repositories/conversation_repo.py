import json
import uuid
import datetime
from typing import List, Optional, Any
from app.db.models.conversation import Conversation, ChatMessage
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: Any):
        super().__init__(Conversation, db)

    async def create_conversation(self, user_id: int, department_id: int, title: str = "New Conversation") -> Conversation:
        conn = self._get_conn()
        conv_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO conversations (id, user_id, department_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?);",
            (conv_id, user_id, department_id, title, now, now)
        )
        return Conversation(id=conv_id, user_id=user_id, department_id=department_id, title=title, created_at=now, updated_at=now)

    async def list_for_user(self, user_id: int) -> List[Conversation]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC;", (user_id,))
        rows = cursor.fetchall()
        return [Conversation.from_row(r) for r in rows]

    async def get_for_user(self, conversation_id: str, user_id: int) -> Optional[Conversation]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ? LIMIT 1;", (conversation_id, user_id))
        row = cursor.fetchone()
        return Conversation.from_row(row) if row else None

    async def add_message(
        self,
        conversation_id: str,
        sender_role: str,
        message: str,
        intent: Optional[str] = None,
        routed_departments: Optional[List[str]] = None,
        evidence_json: Optional[List[dict]] = None
    ) -> ChatMessage:
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        r_depts_str = json.dumps(routed_departments or [])
        ev_str = json.dumps(evidence_json or [])

        cursor = conn.execute(
            """INSERT INTO chat_messages (
                conversation_id, sender_role, message, intent, routed_departments, evidence_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);""",
            (conversation_id, sender_role, message, intent, r_depts_str, ev_str, now)
        )
        # Update conversation updated_at
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?;", (now, conversation_id))

        return ChatMessage(
            id=cursor.lastrowid,
            conversation_id=conversation_id,
            sender_role=sender_role,
            message=message,
            intent=intent,
            routed_departments=routed_departments or [],
            evidence_json=evidence_json or [],
            created_at=now
        )

    async def get_messages(self, conversation_id: str, user_id: int) -> List[ChatMessage]:
        # Validate ownership first
        conv = await self.get_for_user(conversation_id, user_id)
        if not conv:
            return []
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY id ASC;", (conversation_id,))
        rows = cursor.fetchall()
        return [ChatMessage.from_row(r) for r in rows]

    async def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        conv = await self.get_for_user(conversation_id, user_id)
        if not conv:
            return False
        conn = self._get_conn()
        conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?;", (conversation_id, user_id))
        return True
