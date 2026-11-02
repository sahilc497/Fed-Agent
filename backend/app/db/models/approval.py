import json
import uuid
from typing import Optional, Dict, Any
from app.db.base import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    def __init__(
        self,
        id: Optional[str] = None,
        requester_id: int = 1,
        requester_department_id: int = 1,
        action_type: str = "sensitive_operation",
        target_resource: str = "",
        requested_operation: str = "",
        payload: Optional[Any] = None,
        status: str = "pending",
        approver_id: Optional[int] = None,
        decision_reason: Optional[str] = None,
        execution_result: Optional[Any] = None,
        idempotency_key: Optional[str] = None,
        created_at: Optional[Any] = None,
        decided_at: Optional[Any] = None,
        executed_at: Optional[Any] = None,
        expires_at: Optional[Any] = None,
        **kwargs
    ):
        p_data = payload if isinstance(payload, dict) else (json.loads(payload) if isinstance(payload, str) else {})
        res_data = execution_result if isinstance(execution_result, dict) else (json.loads(execution_result) if isinstance(execution_result, str) else execution_result)

        super().__init__(
            id=id or str(uuid.uuid4()),
            requester_id=requester_id,
            requester_department_id=requester_department_id,
            action_type=action_type,
            target_resource=target_resource,
            requested_operation=requested_operation,
            payload=p_data,
            status=status,
            approver_id=approver_id,
            decision_reason=decision_reason,
            execution_result=res_data,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            created_at=created_at,
            decided_at=decided_at,
            executed_at=executed_at,
            expires_at=expires_at,
            **kwargs
        )
