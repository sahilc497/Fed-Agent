import datetime
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.core.logging import get_correlation_id
from app.db.models.federation_request import FederationAccessRequest
from app.db.models.user import User
from app.repositories.federation_repo import FederationRequestRepository
from app.repositories.user_repo import DepartmentRepository, UserRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.business_repo import (
    SalesRepository,
    HRRepository,
    FinanceRepository,
    OperationsRepository
)
from app.schemas.federation import (
    FederationRequestCreate,
    FederationRequestDecision,
    FederationRequestOut,
    FederationConsumeResult
)

# Explicit allowed fields per department to prevent arbitrary SQL or invalid queries
DEPARTMENT_EXPOSED_FIELDS = {
    "sales": {"id", "title", "client_name", "deal_value", "stage", "finance_status", "created_at"},
    "hr": {"id", "employee_code", "full_name", "position", "leave_balance", "performance_rating"},
    "finance": {"id", "invoice_number", "client_name", "amount", "status", "due_date", "related_opportunity_id"},
    "operations": {"id", "sku", "item_name", "category", "quantity_on_hand", "reorder_threshold", "warehouse_location", "status"}
}

STRICTLY_FORBIDDEN_FIELDS = {
    "salary", "compensation", "bank_details", "tax_returns", "internal_reserves", "password", "hashed_password"
}


class FederationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fed_repo = FederationRequestRepository(db)
        self.dept_repo = DepartmentRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)
        self.sales_repo = SalesRepository(db)
        self.hr_repo = HRRepository(db)
        self.finance_repo = FinanceRepository(db)
        self.ops_repo = OperationsRepository(db)

    async def create_request(self, requester: User, data: FederationRequestCreate) -> FederationRequestOut:
        cid = get_correlation_id()
        user_dept = await self.dept_repo.get_by_id(requester.department_id)
        requester_dept_code = user_dept.code if user_dept else "unknown"

        source_dept = await self.dept_repo.get_by_code(data.source_department_code.lower())
        if not source_dept:
            raise NotFoundError(f"Source department '{data.source_department_code}' not found.")

        # Disallow request if requester already belongs to the source department
        if requester.department_id == source_dept.id and requester.role != "admin":
            raise PermissionDeniedError("Cannot submit cross-department request for your own department.")

        # Security check: Check for strictly forbidden fields (e.g. salary)
        req_fields_set = set(data.requested_fields)
        forbidden_hits = req_fields_set.intersection(STRICTLY_FORBIDDEN_FIELDS)
        if forbidden_hits:
            raise PermissionDeniedError(
                f"Requested fields contain strictly forbidden attributes: {list(forbidden_hits)}. Request rejected."
            )

        # Validate that requested fields are legitimate for the target department
        target_allowed = DEPARTMENT_EXPOSED_FIELDS.get(source_dept.code, set())
        invalid_fields = req_fields_set - target_allowed
        if invalid_fields:
            raise PermissionDeniedError(
                f"Invalid fields for department '{source_dept.code}': {list(invalid_fields)}."
            )

        idempotency_key = data.idempotency_key or f"fed-{requester.id}-{source_dept.id}-{uuid.uuid4()}"
        existing = await self.fed_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return await self._to_out_dto(existing)

        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=data.access_duration_minutes or 60
        )

        req_agent = f"{requester_dept_code}_agent"

        req = FederationAccessRequest(
            id=str(uuid.uuid4()),
            requester_user_id=requester.id,
            requester_department_id=requester.department_id,
            requesting_agent=req_agent,
            source_department_id=source_dept.id,
            business_purpose=data.business_purpose,
            requested_fields=data.requested_fields,
            record_identifiers=data.record_identifiers or [],
            access_duration_minutes=data.access_duration_minutes or 60,
            status="PENDING",
            idempotency_key=idempotency_key,
            expires_at=expires_at
        )
        created = await self.fed_repo.create(req)

        await self.audit_repo.log_event(
            action="federation:request_created",
            resource_type=f"cross_dept:{source_dept.code}",
            outcome="allow",
            reason=f"Federation access request created for purpose: {data.business_purpose}",
            correlation_id=cid,
            actor_id=requester.id,
            actor_email=requester.email,
            actor_role=requester.role,
            actor_department=requester_dept_code,
            resource_id=created.id,
            details={
                "from_department": requester_dept_code,
                "to_department": source_dept.code,
                "requested_fields": data.requested_fields,
                "record_identifiers": data.record_identifiers
            }
        )
        await self.db.commit()
        return await self._to_out_dto(created)

    async def list_requests(self, user: User, status: Optional[str] = None) -> List[FederationRequestOut]:
        dept_id = None if user.role == "admin" else user.department_id
        requests = await self.fed_repo.list_requests(department_id=dept_id, status=status)
        return [await self._to_out_dto(r) for r in requests]

    async def get_request(self, request_id: str, user: User) -> FederationRequestOut:
        req = await self.fed_repo.get_by_id(request_id)
        if not req:
            raise NotFoundError("Federation access request not found.")
        if user.role != "admin" and user.department_id not in [req.requester_department_id, req.source_department_id]:
            raise PermissionDeniedError("Cannot inspect federation request of an unrelated department.")
        return await self._to_out_dto(req)

    async def decide_request(
        self,
        request_id: str,
        approver: User,
        data: FederationRequestDecision
    ) -> FederationRequestOut:
        cid = get_correlation_id()
        user_dept = await self.dept_repo.get_by_id(approver.department_id)
        dept_code = user_dept.code if user_dept else "unknown"

        req = await self.fed_repo.get_by_id(request_id)
        if not req:
            raise NotFoundError("Federation access request not found.")

        # Only authorized administrators can approve/reject cross-department federation requests
        if approver.role != "admin":
            raise PermissionDeniedError("Only an authorized Administrator can approve cross-department federation requests.")

        # Requester cannot self-approve
        if req.requester_user_id == approver.id:
            raise PermissionDeniedError("Self-approval is forbidden: Requester cannot approve their own federation request.")

        # Check expiration
        now = datetime.datetime.now(datetime.timezone.utc)
        if req.expires_at < now:
            req.status = "EXPIRED"
            await self.db.commit()
            raise PermissionDeniedError("Cannot decide request: it has already expired.")

        if req.status != "PENDING":
            raise PermissionDeniedError(f"Cannot decide request: already in status '{req.status}'.")

        decision_str = data.decision.lower().strip()
        new_status = "APPROVED" if decision_str == "approve" else "REJECTED"

        approved_fields = data.approved_fields or req.requested_fields
        # Strip any forbidden fields that may have somehow appeared
        approved_fields = [f for f in approved_fields if f not in STRICTLY_FORBIDDEN_FIELDS]
        approved_records = data.approved_record_ids or req.record_identifiers

        updated = await self.fed_repo.mark_decision(
            request_id=request_id,
            status=new_status,
            approver_id=approver.id,
            reason=data.reason,
            approved_fields=approved_fields,
            approved_record_ids=approved_records
        )

        await self.audit_repo.log_event(
            action=f"federation:{new_status.lower()}",
            resource_type="federation_grant",
            outcome="allow",
            reason=data.reason or f"Federation request {new_status}",
            correlation_id=cid,
            actor_id=approver.id,
            actor_email=approver.email,
            actor_role=approver.role,
            actor_department=dept_code,
            resource_id=request_id,
            details={
                "status": new_status,
                "approved_fields": approved_fields,
                "requester_id": req.requester_user_id
            }
        )
        await self.db.commit()
        return await self._to_out_dto(updated)

    async def revoke_request(self, request_id: str, admin: User, reason: Optional[str] = None) -> FederationRequestOut:
        cid = get_correlation_id()
        if admin.role != "admin":
            raise PermissionDeniedError("Only an Administrator can revoke federation access grants.")

        req = await self.fed_repo.get_by_id(request_id)
        if not req:
            raise NotFoundError("Federation access request not found.")

        updated = await self.fed_repo.mark_revoked(request_id)

        await self.audit_repo.log_event(
            action="federation:revoked",
            resource_type="federation_grant",
            outcome="allow",
            reason=reason or "Administrator revoked federation access grant.",
            correlation_id=cid,
            actor_id=admin.id,
            actor_email=admin.email,
            actor_role=admin.role,
            actor_department="admin",
            resource_id=request_id
        )
        await self.db.commit()
        return await self._to_out_dto(updated)

    async def consume_request(self, request_id: str, caller: User) -> FederationConsumeResult:
        """
        Federation Gateway execution: validates that the grant is APPROVED, unexpired,
        unrevoked, matches the caller, and retrieves ONLY the approved fields from the source department.
        """
        cid = get_correlation_id()
        req = await self.fed_repo.get_by_id(request_id)
        if not req:
            raise NotFoundError("Federation access request not found.")

        # Check caller authorized to consume (caller must be requester, admin, or in requester department)
        if caller.role != "admin" and caller.department_id != req.requester_department_id:
            raise PermissionDeniedError("Caller is not authorized to consume this federation grant.")

        # Check status
        if req.status != "APPROVED":
            raise PermissionDeniedError(f"Cannot consume federation request: status is '{req.status}', must be 'APPROVED'.")

        # Check expiry
        now = datetime.datetime.now(datetime.timezone.utc)
        if req.expires_at < now:
            req.status = "EXPIRED"
            await self.db.commit()
            raise PermissionDeniedError("Federation access grant has expired.")

        # Check revocation
        if req.revoked_at is not None:
            raise PermissionDeniedError("Federation access grant has been revoked.")

        source_dept = await self.dept_repo.get_by_id(req.source_department_id)
        source_code = source_dept.code if source_dept else "unknown"

        allowed_fields = set(req.approved_fields or req.requested_fields)
        # Final strict guard: never allow forbidden fields
        allowed_fields = allowed_fields - STRICTLY_FORBIDDEN_FIELDS

        # Fetch matching records from source department
        records_data = await self._fetch_source_records(
            source_dept_code=source_code,
            dept_id=req.source_department_id,
            allowed_fields=allowed_fields,
            record_identifiers=req.approved_record_ids or req.record_identifiers or []
        )

        # Mark completed or update used_at
        await self.fed_repo.mark_completed(request_id)

        # Audit data release
        await self.audit_repo.log_event(
            action="gateway:data_release",
            resource_type=f"cross_dept:{source_code}",
            outcome="allow",
            reason=f"Federation Gateway released {len(records_data)} records for grant {request_id}",
            correlation_id=cid,
            actor_id=caller.id,
            actor_email=caller.email,
            actor_role=caller.role,
            actor_department=str(caller.department_id),
            resource_id=request_id,
            details={
                "source_department": source_code,
                "released_fields": list(allowed_fields),
                "record_count": len(records_data)
            }
        )
        await self.db.commit()

        return FederationConsumeResult(
            request_id=request_id,
            status="COMPLETED",
            source_department=source_code,
            released_fields=list(allowed_fields),
            record_count=len(records_data),
            records=records_data
        )

    async def _fetch_source_records(
        self,
        source_dept_code: str,
        dept_id: int,
        allowed_fields: set[str],
        record_identifiers: List[str]
    ) -> List[Dict[str, Any]]:
        results = []
        if source_dept_code == "finance":
            invoices = await self.finance_repo.list_invoices(department_id=dept_id)
            if record_identifiers:
                invoices = [inv for inv in invoices if inv.invoice_number in record_identifiers or str(inv.id) in record_identifiers]
            for inv in invoices:
                item = {}
                if "id" in allowed_fields: item["id"] = inv.id
                if "invoice_number" in allowed_fields: item["invoice_number"] = inv.invoice_number
                if "client_name" in allowed_fields: item["client_name"] = inv.client_name
                if "amount" in allowed_fields: item["amount"] = inv.amount
                if "status" in allowed_fields: item["status"] = inv.status
                if "due_date" in allowed_fields: item["due_date"] = inv.due_date.isoformat()
                if "related_opportunity_id" in allowed_fields: item["related_opportunity_id"] = inv.related_opportunity_id
                results.append(item)

        elif source_dept_code == "sales":
            opps = await self.sales_repo.list_for_department(department_id=dept_id)
            if record_identifiers:
                opps = [op for op in opps if op.title in record_identifiers or str(op.id) in record_identifiers]
            for op in opps:
                item = {}
                if "id" in allowed_fields: item["id"] = op.id
                if "title" in allowed_fields: item["title"] = op.title
                if "client_name" in allowed_fields: item["client_name"] = op.client_name
                if "deal_value" in allowed_fields: item["deal_value"] = op.deal_value
                if "stage" in allowed_fields: item["stage"] = op.stage
                if "finance_status" in allowed_fields: item["finance_status"] = op.finance_status
                if "created_at" in allowed_fields: item["created_at"] = op.created_at.isoformat()
                results.append(item)

        elif source_dept_code == "hr":
            employees = await self.hr_repo.list_employees(department_id=dept_id)
            if record_identifiers:
                employees = [e for e in employees if e.employee_code in record_identifiers or str(e.id) in record_identifiers]
            for emp in employees:
                item = {}
                if "id" in allowed_fields: item["id"] = emp.id
                if "employee_code" in allowed_fields: item["employee_code"] = emp.employee_code
                if "full_name" in allowed_fields: item["full_name"] = emp.full_name
                if "position" in allowed_fields: item["position"] = emp.position
                if "leave_balance" in allowed_fields: item["leave_balance"] = emp.leave_balance
                if "performance_rating" in allowed_fields: item["performance_rating"] = emp.performance_rating
                # Never include salary in cross-department release!
                results.append(item)

        elif source_dept_code == "operations":
            items = await self.ops_repo.list_items(department_id=dept_id)
            if record_identifiers:
                items = [it for it in items if it.sku in record_identifiers or str(it.id) in record_identifiers]
            for it in items:
                row = {}
                if "id" in allowed_fields: row["id"] = it.id
                if "sku" in allowed_fields: row["sku"] = it.sku
                if "item_name" in allowed_fields: row["item_name"] = it.item_name
                if "category" in allowed_fields: row["category"] = it.category
                if "quantity_on_hand" in allowed_fields: row["quantity_on_hand"] = it.quantity_on_hand
                if "reorder_threshold" in allowed_fields: row["reorder_threshold"] = it.reorder_threshold
                if "warehouse_location" in allowed_fields: row["warehouse_location"] = it.warehouse_location
                if "status" in allowed_fields: row["status"] = it.status
                results.append(row)

        return results

    async def _to_out_dto(self, req: FederationAccessRequest) -> FederationRequestOut:
        dto = FederationRequestOut.model_validate(req)
        # Populate email and dept codes
        u = await self.user_repo.get_by_id(req.requester_user_id)
        if u:
            dto.requester_email = u.email
        src_d = await self.dept_repo.get_by_id(req.source_department_id)
        if src_d:
            dto.source_department_code = src_d.code
        req_d = await self.dept_repo.get_by_id(req.requester_department_id)
        if req_d:
            dto.requester_department_code = req_d.code
        return dto
