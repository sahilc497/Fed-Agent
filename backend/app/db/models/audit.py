import json
from typing import Optional, Dict, Any
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    def __init__(
        self,
        id: Optional[int] = None,
        timestamp: Optional[Any] = None,
        action: str = "",
        resource_type: str = "",
        outcome: str = "allow",
        reason: str = "",
        correlation_id: str = "",
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = None,
        actor_role: str = "system",
        actor_department: str = "system",
        resource_id: Optional[str] = None,
        gateway_decision: Optional[Any] = None,
        details: Optional[Any] = None,
        **kwargs
    ):
        gw = gateway_decision if isinstance(gateway_decision, dict) else (json.loads(gateway_decision) if isinstance(gateway_decision, str) else gateway_decision)
        det = details if isinstance(details, dict) else (json.loads(details) if isinstance(details, str) else {})

        super().__init__(
            id=id,
            timestamp=timestamp,
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
            gateway_decision=gw,
            details=det,
            **kwargs
        )
