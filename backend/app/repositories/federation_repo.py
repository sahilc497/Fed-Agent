import json
import datetime
from typing import List, Optional, Any
from app.db.models.federation_request import FederationAccessRequest
from app.repositories.base import BaseRepository


class FederationRequestRepository(BaseRepository[FederationAccessRequest]):
    def __init__(self, db: Any):
        super().__init__(FederationAccessRequest, db)

    async def get_by_id(self, request_id: str) -> Optional[FederationAccessRequest]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM federation_access_requests WHERE id = ? LIMIT 1;", (request_id,))
        row = cursor.fetchone()
        return FederationAccessRequest.from_row(row) if row else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[FederationAccessRequest]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM federation_access_requests WHERE idempotency_key = ? LIMIT 1;", (idempotency_key,))
        row = cursor.fetchone()
        return FederationAccessRequest.from_row(row) if row else None

    async def list_requests(
        self,
        department_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[FederationAccessRequest]:
        conn = self._get_conn()
        query = "SELECT * FROM federation_access_requests"
        clauses = []
        params = []
        if department_id is not None:
            clauses.append("(requester_department_id = ? OR source_department_id = ?)")
            params.extend([department_id, department_id])
        if status:
            clauses.append("status = ?")
            params.append(status.upper())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, rowid DESC;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [FederationAccessRequest.from_row(r) for r in rows]

    async def mark_decision(
        self,
        request_id: str,
        status: str,
        approver_id: int,
        reason: Optional[str] = None,
        approved_fields: Optional[List[str]] = None,
        approved_record_ids: Optional[List[str]] = None,
        expires_at: Optional[str] = None
    ) -> Optional[FederationAccessRequest]:
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        app_f_str = json.dumps(approved_fields) if approved_fields is not None else None
        app_rec_str = json.dumps(approved_record_ids) if approved_record_ids is not None else None

        conn.execute(
            """UPDATE federation_access_requests 
               SET status = ?, approver_user_id = ?, decision_reason = ?,
                   approved_fields = COALESCE(?, approved_fields),
                   approved_record_ids = COALESCE(?, approved_record_ids),
                   decided_at = ?,
                   expires_at = COALESCE(?, expires_at)
               WHERE id = ?;""",
            (status.upper(), approver_id, reason or f"Decision: {status}", app_f_str, app_rec_str, now, expires_at, request_id)
        )
        return await self.get_by_id(request_id)

    async def mark_revoked(self, request_id: str) -> Optional[FederationAccessRequest]:
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            "UPDATE federation_access_requests SET status = 'REVOKED', revoked_at = ? WHERE id = ?;",
            (now, request_id)
        )
        return await self.get_by_id(request_id)

    async def mark_completed(self, request_id: str) -> Optional[FederationAccessRequest]:
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            "UPDATE federation_access_requests SET status = 'COMPLETED', used_at = ? WHERE id = ?;",
            (now, request_id)
        )
        return await self.get_by_id(request_id)
