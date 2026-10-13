import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.federation_request import FederationAccessRequest
from app.repositories.base import BaseRepository


class FederationRequestRepository(BaseRepository[FederationAccessRequest]):
    def __init__(self, db: AsyncSession):
        super().__init__(FederationAccessRequest, db)

    async def get_by_id(self, request_id: str) -> Optional[FederationAccessRequest]:
        stmt = select(FederationAccessRequest).where(FederationAccessRequest.id == request_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[FederationAccessRequest]:
        stmt = select(FederationAccessRequest).where(FederationAccessRequest.idempotency_key == idempotency_key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        department_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[FederationAccessRequest]:
        stmt = select(FederationAccessRequest)
        conditions = []

        if department_id is not None:
            # Users can see requests where their department is either requester or source
            conditions.append(
                or_(
                    FederationAccessRequest.requester_department_id == department_id,
                    FederationAccessRequest.source_department_id == department_id
                )
            )

        if status:
            conditions.append(FederationAccessRequest.status == status.upper())

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(FederationAccessRequest.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_decision(
        self,
        request_id: str,
        status: str,
        approver_id: int,
        reason: Optional[str] = None,
        approved_fields: Optional[List[str]] = None,
        approved_record_ids: Optional[List[str]] = None
    ) -> Optional[FederationAccessRequest]:
        req = await self.get_by_id(request_id)
        if req:
            req.status = status.upper()
            req.approver_user_id = approver_id
            req.decision_reason = reason or f"Decision: {status}"
            req.decided_at = datetime.datetime.now(datetime.timezone.utc)
            if approved_fields is not None:
                req.approved_fields = approved_fields
            if approved_record_ids is not None:
                req.approved_record_ids = approved_record_ids
            await self.db.flush()
        return req

    async def mark_revoked(self, request_id: str) -> Optional[FederationAccessRequest]:
        req = await self.get_by_id(request_id)
        if req:
            req.status = "REVOKED"
            req.revoked_at = datetime.datetime.now(datetime.timezone.utc)
            await self.db.flush()
        return req

    async def mark_completed(self, request_id: str) -> Optional[FederationAccessRequest]:
        req = await self.get_by_id(request_id)
        if req:
            req.status = "COMPLETED"
            req.used_at = datetime.datetime.now(datetime.timezone.utc)
            await self.db.flush()
        return req
