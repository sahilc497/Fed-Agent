import json
import uuid
from typing import Optional, List, Any
from app.db.base import Base


class FederationAccessRequest(Base):
    __tablename__ = "federation_access_requests"

    def __init__(
        self,
        id: Optional[str] = None,
        requester_user_id: int = 1,
        requester_department_id: int = 1,
        requesting_agent: str = "sales_agent",
        source_department_id: int = 3,
        business_purpose: str = "",
        requested_fields: Optional[Any] = None,
        record_identifiers: Optional[Any] = None,
        access_duration_minutes: int = 60,
        status: str = "PENDING",
        approver_user_id: Optional[int] = None,
        decision_reason: Optional[str] = None,
        approved_fields: Optional[Any] = None,
        approved_record_ids: Optional[Any] = None,
        idempotency_key: Optional[str] = None,
        created_at: Optional[Any] = None,
        decided_at: Optional[Any] = None,
        expires_at: Optional[Any] = None,
        revoked_at: Optional[Any] = None,
        used_at: Optional[Any] = None,
        **kwargs
    ):
        # Normalize list/json fields
        req_f = requested_fields if isinstance(requested_fields, list) else (json.loads(requested_fields) if isinstance(requested_fields, str) else [])
        rec_ids = record_identifiers if isinstance(record_identifiers, list) else (json.loads(record_identifiers) if isinstance(record_identifiers, str) else [])
        app_f = approved_fields if isinstance(approved_fields, list) else (json.loads(approved_fields) if isinstance(approved_fields, str) else approved_fields)
        app_rec = approved_record_ids if isinstance(approved_record_ids, list) else (json.loads(approved_record_ids) if isinstance(approved_record_ids, str) else approved_record_ids)

        super().__init__(
            id=id or str(uuid.uuid4()),
            requester_user_id=requester_user_id,
            requester_department_id=requester_department_id,
            requesting_agent=requesting_agent,
            source_department_id=source_department_id,
            business_purpose=business_purpose,
            requested_fields=req_f,
            record_identifiers=rec_ids,
            access_duration_minutes=access_duration_minutes,
            status=status,
            approver_user_id=approver_user_id,
            decision_reason=decision_reason,
            approved_fields=app_f,
            approved_record_ids=app_rec,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            created_at=created_at,
            decided_at=decided_at,
            expires_at=expires_at,
            revoked_at=revoked_at,
            used_at=used_at,
            **kwargs
        )
