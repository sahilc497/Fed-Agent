import json
import datetime
from typing import List, Optional, Any
from app.db.models.approval import ApprovalRequest
from app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[ApprovalRequest]):
    def __init__(self, db: Any):
        super().__init__(ApprovalRequest, db)

    async def get_by_idempotency_key(self, key: str) -> Optional[ApprovalRequest]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM approval_requests WHERE idempotency_key = ? LIMIT 1;", (key,))
        row = cursor.fetchone()
        return ApprovalRequest.from_row(row) if row else None

    async def list_for_department(
        self,
        department_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[ApprovalRequest]:
        conn = self._get_conn()
        query = "SELECT * FROM approval_requests"
        clauses = []
        params = []
        if department_id is not None:
            clauses.append("requester_department_id = ?")
            params.append(department_id)
        if status:
            clauses.append("status = ?")
            params.append(status.lower())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [ApprovalRequest.from_row(r) for r in rows]

    async def mark_decision(
        self,
        approval_id: str,
        status: str,
        approver_id: int,
        reason: Optional[str] = None
    ) -> Optional[ApprovalRequest]:
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            """UPDATE approval_requests 
               SET status = ?, approver_id = ?, decision_reason = ?, decided_at = ?
               WHERE id = ?;""",
            (status.lower(), approver_id, reason, now, approval_id)
        )
        return await self.get_by_id(approval_id)

    async def mark_executed(
        self,
        approval_id: str,
        result: dict
    ) -> Optional[ApprovalRequest]:
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            """UPDATE approval_requests 
               SET status = 'executed', executed_at = ?, execution_result = ?
               WHERE id = ?;""",
            (now, json.dumps(result), approval_id)
        )
        return await self.get_by_id(approval_id)
