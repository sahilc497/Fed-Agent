import datetime
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import PermissionDeniedError, NotFoundError, ApprovalRequiredError
from app.core.logging import get_correlation_id
from app.db.models.approval import ApprovalRequest
from app.db.models.user import User
from app.repositories.approval_repo import ApprovalRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import DepartmentRepository
from app.schemas.approval import ApprovalCreate, ApprovalOut


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.approval_repo = ApprovalRepository(db)
        self.audit_repo = AuditRepository(db)
        self.dept_repo = DepartmentRepository(db)

    async def create_approval_request(self, requester: User, data: ApprovalCreate) -> ApprovalOut:
        cid = get_correlation_id()
        user_dept = await self.dept_repo.get_by_id(requester.department_id)
        dept_code = user_dept.code if user_dept else "unknown"

        idempotency_key = data.idempotency_key or str(uuid.uuid4())
        existing = await self.approval_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return ApprovalOut.model_validate(existing)

        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.APPROVAL_EXPIRY_MINUTES
        )

        req = ApprovalRequest(
            id=str(uuid.uuid4()),
            requester_id=requester.id,
            requester_department_id=requester.department_id,
            action_type=data.action_type,
            target_resource=data.target_resource,
            requested_operation=data.requested_operation,
            payload=data.payload,
            status="pending",
            idempotency_key=idempotency_key,
            expires_at=expires_at
        )
        created = await self.approval_repo.create(req)

        await self.audit_repo.log_event(
            action="approval_request:created",
            resource_type="approval",
            outcome="allow",
            reason=f"Human approval requested for sensitive action: {data.action_type}",
            correlation_id=cid,
            actor_id=requester.id,
            actor_email=requester.email,
            actor_role=requester.role,
            actor_department=dept_code,
            resource_id=created.id,
            details={"action_type": data.action_type, "target": data.target_resource}
        )
        await self.db.commit()
        return ApprovalOut.model_validate(created)

    async def list_approvals(self, user: User, status: Optional[str] = None) -> List[ApprovalOut]:
        dept_id = None if user.role == "admin" else user.department_id
        requests = await self.approval_repo.list_for_department(department_id=dept_id, status=status)
        return [ApprovalOut.model_validate(r) for r in requests]

    async def get_approval(self, approval_id: str, user: User) -> ApprovalOut:
        req = await self.approval_repo.get_by_id(approval_id)
        if not req:
            raise NotFoundError("Approval request not found.")
        if user.role != "admin" and req.requester_department_id != user.department_id:
            raise PermissionDeniedError("Cannot inspect approval request of another department.")
        return ApprovalOut.model_validate(req)

    async def decide_approval(self, approval_id: str, approver: User, decision: str, reason: Optional[str] = None) -> ApprovalOut:
        cid = get_correlation_id()
        user_dept = await self.dept_repo.get_by_id(approver.department_id)
        dept_code = user_dept.code if user_dept else "unknown"

        req = await self.approval_repo.get_by_id(approval_id)
        if not req:
            raise NotFoundError("Approval request not found.")

        # Check expiration
        now = datetime.datetime.now(datetime.timezone.utc)
        if req.expires_at < now:
            req.status = "expired"
            await self.db.commit()
            raise PermissionDeniedError("Approval request has expired.")

        if req.status != "pending":
            raise PermissionDeniedError(f"Cannot decide approval: request already in state '{req.status}'.")

        # Safeguard: Requester cannot self-approve
        if settings.PREVENT_SELF_APPROVAL and req.requester_id == approver.id:
            raise PermissionDeniedError("Self-approval is forbidden: Requester cannot approve their own sensitive operation.")

        # Safeguard: Role check
        if approver.role not in ["admin", "department_manager"]:
            raise PermissionDeniedError("Only Department Managers and Administrators may decide approvals.")

        # Safeguard: Department boundary
        if approver.role != "admin" and req.requester_department_id != approver.department_id:
            raise PermissionDeniedError("Department Manager can only approve requests from their own department.")

        new_status = "approved" if decision.lower() == "approve" else "rejected"
        updated = await self.approval_repo.mark_decision(approval_id, new_status, approver.id)

        await self.audit_repo.log_event(
            action=f"approval_request:{new_status}",
            resource_type="approval",
            outcome="allow",
            reason=reason or f"Approval decision: {new_status}",
            correlation_id=cid,
            actor_id=approver.id,
            actor_email=approver.email,
            actor_role=approver.role,
            actor_department=dept_code,
            resource_id=approval_id,
            details={"decision": new_status, "requester_id": req.requester_id}
        )
        await self.db.commit()
        return ApprovalOut.model_validate(updated)

    async def execute_approved_action(self, approval_id: str, executor: User) -> Dict[str, Any]:
        cid = get_correlation_id()
        user_dept = await self.dept_repo.get_by_id(executor.department_id)
        dept_code = user_dept.code if user_dept else "unknown"

        req = await self.approval_repo.get_by_id(approval_id)
        if not req:
            raise NotFoundError("Approval request not found.")

        if req.status != "approved":
            raise PermissionDeniedError(f"Cannot execute: approval status is '{req.status}', must be 'approved'.")

        if req.executed_at is not None:
            raise PermissionDeniedError("Duplicate execution prevented: this action has already been executed.")

        # Execute simulated safe business operation
        execution_result = {
            "execution_status": "success",
            "mode": "simulated_development_mode",
            "action_type": req.action_type,
            "target_resource": req.target_resource,
            "message": f"Successfully executed approved operation for {req.target_resource} (Simulated Enterprise Action)."
        }

        updated = await self.approval_repo.mark_executed(approval_id, execution_result)

        await self.audit_repo.log_event(
            action="approval_request:executed",
            resource_type="approval",
            outcome="allow",
            reason=f"Executed approved action: {req.action_type}",
            correlation_id=cid,
            actor_id=executor.id,
            actor_email=executor.email,
            actor_role=executor.role,
            actor_department=dept_code,
            resource_id=approval_id,
            details=execution_result
        )
        await self.db.commit()

        return execution_result
