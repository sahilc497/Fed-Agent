import json
import datetime
from typing import List, Optional, Any
from app.db.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Any):
        super().__init__(AuditLog, db)

    async def log_event(
        self,
        action: str,
        resource_type: str,
        outcome: str,
        reason: str,
        correlation_id: str,
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = None,
        actor_role: str = "system",
        actor_department: str = "system",
        resource_id: Optional[str] = None,
        gateway_decision: Optional[dict] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """Appends an immutable audit event record to SQLite."""
        conn = self._get_conn()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        gw_str = json.dumps(gateway_decision) if gateway_decision is not None else None
        det_str = json.dumps(details or {})

        cursor = conn.execute(
            """INSERT INTO audit_logs (
                timestamp, action, resource_type, outcome, reason, correlation_id,
                actor_id, actor_email, actor_role, actor_department, resource_id,
                gateway_decision, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
            (
                now, action, resource_type, outcome, reason, correlation_id,
                actor_id, actor_email, actor_role, actor_department, resource_id,
                gw_str, det_str
            )
        )
        return AuditLog(
            id=cursor.lastrowid,
            timestamp=now,
            action=action,
            resource_type=resource_type,
            outcome=outcome,
            reason=reason,
            correlation_id=correlation_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            actor_department=actor_department,
            resource_id=resource_id,
            gateway_decision=gateway_decision,
            details=details or {}
        )

    async def list_audit_logs(
        self,
        department: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        conn = self._get_conn()
        query = "SELECT * FROM audit_logs"
        clauses = []
        params = []
        if department and department != "all":
            clauses.append("actor_department = ?")
            params.append(department)
        if action:
            clauses.append("action = ?")
            params.append(action)
        if outcome:
            clauses.append("outcome = ?")
            params.append(outcome)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ? OFFSET ?;"
        params.extend([limit, skip])

        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [AuditLog.from_row(r) for r in rows]
