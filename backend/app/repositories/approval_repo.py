import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.approval import ApprovalRequest
from app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[ApprovalRequest]):
    def __init__(self, db: AsyncSession):
        super().__init__(ApprovalRequest, db)

    async def get_by_idempotency_key(self, key: str) -> Optional[ApprovalRequest]:
        stmt = select(ApprovalRequest).where(ApprovalRequest.idempotency_key == key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_department(
        self,
        department_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[ApprovalRequest]:
        stmt = select(ApprovalRequest)
        conditions = []
        if department_id:
            conditions.append(ApprovalRequest.requester_department_id == department_id)
        if status:
            conditions.append(ApprovalRequest.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(ApprovalRequest.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_decision(
        self,
        approval_id: str,
        status: str,  # approved or rejected
        approver_id: int
    ) -> Optional[ApprovalRequest]:
        req = await self.get_by_id(approval_id)
        if not req:
            return None
        now = datetime.datetime.now(datetime.timezone.utc)
        req.status = status
        req.approver_id = approver_id
        req.decided_at = now
        await self.db.flush()
        return req

    async def mark_executed(
        self,
        approval_id: str,
        result: dict
    ) -> Optional[ApprovalRequest]:
        req = await self.get_by_id(approval_id)
        if not req:
            return None
        now = datetime.datetime.now(datetime.timezone.utc)
        req.executed_at = now
        req.execution_result = result
        await self.db.flush()
        return req
