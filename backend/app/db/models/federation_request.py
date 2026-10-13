import datetime
import uuid
from typing import Optional, List
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class FederationAccessRequest(Base):
    __tablename__ = "federation_access_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    requester_department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    requesting_agent: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., sales_agent, operations_agent
    source_department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    business_purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_fields: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # list of field names
    record_identifiers: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # list of record IDs / filter keys
    access_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    # Statuses: PENDING, APPROVED, REJECTED, EXPIRED, REVOKED, COMPLETED
    approver_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_fields: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    approved_record_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
