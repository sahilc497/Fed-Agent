import logging
from typing import Any, Dict, List, Optional
from app.core.exceptions import GatewayPolicyError
from app.db.models.user import User
from app.gateway.schemas import FederationRequest, FederationResponse
from app.repositories.audit_repo import AuditRepository
from app.repositories.business_repo import SalesRepository, HRRepository, FinanceRepository, OperationsRepository

logger = logging.getLogger("federated_mesh.gateway")

# Explicit Cross-Department Policy Contracts
PERMITTED_POLICIES = {
    ("sales", "finance"): {
        "allowed_purposes": ["opportunity_finance_status", "invoice_status_check", "order_validation"],
        "allowed_fields": {"opportunity_id", "finance_status", "invoice_number", "status", "due_date", "deal_value"},
        "strictly_forbidden_fields": {"profit_margin", "internal_reserves", "bank_details", "tax_returns"}
    },
    ("hr", "finance"): {
        "allowed_purposes": ["payroll_verification", "benefits_billing"],
        "allowed_fields": {"invoice_number", "payment_reference", "status"},
        "strictly_forbidden_fields": {"client_contracts", "executive_compensation"}
    },
    ("finance", "sales"): {
        "allowed_purposes": ["deal_verification", "client_history"],
        "allowed_fields": {"client_name", "title", "deal_value", "stage"},
        "strictly_forbidden_fields": {"confidential_notes"}
    },
    ("sales", "operations"): {
        "allowed_purposes": ["inventory_check", "shipping_status"],
        "allowed_fields": {"sku", "item_name", "quantity_on_hand", "status", "warehouse_location"},
        "strictly_forbidden_fields": {"supplier_margins", "warehouse_lease_costs"}
    },
    ("operations", "finance"): {
        "allowed_purposes": ["purchase_order_invoicing", "procurement_status"],
        "allowed_fields": {"invoice_number", "status", "due_date"},
        "strictly_forbidden_fields": {"executive_bonuses", "bank_account"}
    },
    ("operations", "sales"): {
        "allowed_purposes": ["order_fulfillment_status", "delivery_confirmation"],
        "allowed_fields": {"title", "client_name", "stage"},
        "strictly_forbidden_fields": {"commissions", "confidential_deal_notes"}
    },
    ("finance", "operations"): {
        "allowed_purposes": ["asset_valuation", "inventory_audit"],
        "allowed_fields": {"sku", "item_name", "quantity_on_hand", "status"},
        "strictly_forbidden_fields": {"shift_schedules"}
    }
}


class FederationGatewayService:
    def __init__(self, db: Any):
        self.db = db
        self.audit_repo = AuditRepository(db)
        self.sales_repo = SalesRepository(db)
        self.hr_repo = HRRepository(db)
        self.finance_repo = FinanceRepository(db)
        self.ops_repo = OperationsRepository(db)


    async def execute_federated_request(
        self,
        user: User,
        request: FederationRequest
    ) -> FederationResponse:
        """
        Critical security boundary: Enforces cross-department federation policies.
        Rejects prohibited fields, checks target contracts, and audits all decisions.
        """
        req_pair = (request.requesting_department, request.target_department)

        # 1. Reject if no federation agreement exists for this pair
        if req_pair not in PERMITTED_POLICIES:
            reason = f"No federation policy exists allowing {request.requesting_department} to query {request.target_department}."
            await self._audit_decision(request, user, outcome="deny", reason=reason)
            return FederationResponse(
                request_id=request.request_id,
                is_allowed=False,
                status_code=403,
                policy_reason=reason,
                denied_fields=request.requested_fields,
                correlation_id=request.correlation_id
            )

        policy = PERMITTED_POLICIES[req_pair]

        # 2. Check Purpose
        if request.business_purpose not in policy["allowed_purposes"]:
            reason = f"Business purpose '{request.business_purpose}' is not authorized for cross-department bridge {req_pair}."
            await self._audit_decision(request, user, outcome="deny", reason=reason)
            return FederationResponse(
                request_id=request.request_id,
                is_allowed=False,
                status_code=403,
                policy_reason=reason,
                denied_fields=request.requested_fields,
                correlation_id=request.correlation_id
            )

        # 3. Check for explicitly forbidden fields (e.g. salary, reserves)
        requested_set = set(request.requested_fields)
        forbidden_hits = requested_set.intersection(policy["strictly_forbidden_fields"])
        if forbidden_hits or "salary" in requested_set or "compensation" in requested_set:
            reason = f"Explicitly forbidden fields requested: {list(forbidden_hits or ['salary'])}. Immediate denial."
            await self._audit_decision(request, user, outcome="deny", reason=reason)
            return FederationResponse(
                request_id=request.request_id,
                is_allowed=False,
                status_code=403,
                policy_reason=reason,
                denied_fields=list(forbidden_hits or ["salary"]),
                correlation_id=request.correlation_id
            )

        # 4. Filter to permitted fields only
        allowed_fields = requested_set.intersection(policy["allowed_fields"])
        denied_fields = list(requested_set - allowed_fields)

        if not allowed_fields:
            reason = "None of the requested fields are permitted by the federation agreement."
            await self._audit_decision(request, user, outcome="deny", reason=reason)
            return FederationResponse(
                request_id=request.request_id,
                is_allowed=False,
                status_code=403,
                policy_reason=reason,
                denied_fields=denied_fields,
                correlation_id=request.correlation_id
            )

        # 5. Fetch and filter minimal data from the target department
        filtered_results = await self._fetch_federated_data(request.target_department, allowed_fields)

        reason = f"Authorized cross-department federation query granted. Allowed fields: {list(allowed_fields)}."
        await self._audit_decision(
            request,
            user,
            outcome="allow",
            reason=reason,
            gateway_data={"allowed_fields": list(allowed_fields), "result_count": len(filtered_results)}
        )

        return FederationResponse(
            request_id=request.request_id,
            is_allowed=True,
            status_code=200,
            policy_reason=reason,
            filtered_data=filtered_results,
            denied_fields=denied_fields,
            correlation_id=request.correlation_id
        )

    async def _fetch_federated_data(
        self,
        target_department: str,
        allowed_fields: set[str]
    ) -> List[Dict[str, Any]]:
        results = []
        if target_department == "finance":
            # Return invoices or finance approval status
            invoices = await self.finance_repo.list_all(limit=20)
            for inv in invoices:
                item = {}
                if "invoice_number" in allowed_fields:
                    item["invoice_number"] = inv.invoice_number
                if "status" in allowed_fields:
                    item["status"] = inv.status
                if "due_date" in allowed_fields:
                    item["due_date"] = str(inv.due_date)
                if "opportunity_id" in allowed_fields:
                    item["opportunity_id"] = inv.related_opportunity_id
                results.append(item)
        elif target_department == "sales":
            opps = await self.sales_repo.list_all(limit=20)
            for op in opps:
                item = {}
                if "client_name" in allowed_fields:
                    item["client_name"] = op.client_name
                if "title" in allowed_fields:
                    item["title"] = op.title
                if "deal_value" in allowed_fields:
                    item["deal_value"] = op.deal_value
                if "stage" in allowed_fields:
                    item["stage"] = op.stage
                if "finance_status" in allowed_fields:
                    item["finance_status"] = op.finance_status
                results.append(item)
        elif target_department == "operations":
            items = await self.ops_repo.list_all(limit=20)
            for it in items:
                item = {}
                if "sku" in allowed_fields:
                    item["sku"] = it.sku
                if "item_name" in allowed_fields:
                    item["item_name"] = it.item_name
                if "category" in allowed_fields:
                    item["category"] = it.category
                if "quantity_on_hand" in allowed_fields:
                    item["quantity_on_hand"] = it.quantity_on_hand
                if "warehouse_location" in allowed_fields:
                    item["warehouse_location"] = it.warehouse_location
                if "status" in allowed_fields:
                    item["status"] = it.status
                results.append(item)

        return results


    async def _audit_decision(
        self,
        request: FederationRequest,
        user: User,
        outcome: str,
        reason: str,
        gateway_data: Optional[Dict[str, Any]] = None
    ) -> None:
        await self.audit_repo.log_event(
            action="gateway:federated_request",
            resource_type=f"cross_dept:{request.target_department}",
            outcome=outcome,
            reason=reason,
            correlation_id=request.correlation_id,
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role,
            actor_department=request.requesting_department,
            gateway_decision={
                "from_department": request.requesting_department,
                "to_department": request.target_department,
                "purpose": request.business_purpose,
                "requested_fields": request.requested_fields,
                "decision": outcome
            },
            details=gateway_data or {}
        )
        await self.db.commit()

