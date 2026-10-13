from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(AuditLog, db)

    async def log_event(
        self,
        action: str,
        resource_type: str,
        outcome: str,  # allow, deny, error
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
        """Appends an immutable audit event record."""
        log = AuditLog(
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
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_audit_logs(
        self,
        department: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        stmt = select(AuditLog)
        conditions = []
        if department and department != "all":
            conditions.append(AuditLog.actor_department == department)
        if action:
            conditions.append(AuditLog.action == action)
        if outcome:
            conditions.append(AuditLog.outcome == outcome)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
