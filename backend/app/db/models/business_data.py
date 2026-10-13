import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    deal_value: Mapped[float] = mapped_column(Float, nullable=False)
    stage: Mapped[str] = mapped_column(String(50), default="lead", nullable=False)  # lead, qualified, proposal, closed_won, closed_lost
    needs_finance_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finance_status: Mapped[str] = mapped_column(String(50), default="none", nullable=False)  # none, pending, approved, rejected
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )


class HREmployeeRecord(Base):
    __tablename__ = "hr_employee_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    leave_balance: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)  # Classified / sensitive
    performance_rating: Mapped[str] = mapped_column(String(50), default="Satisfactory", nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )


class HRLeaveRecord(Base):
    __tablename__ = "hr_leave_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("hr_employee_records.id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)  # annual, sick, personal
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="approved", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )


class FinanceInvoice(Base):
    __tablename__ = "finance_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False)  # draft, sent, paid, overdue, pending_approval
    due_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    related_opportunity_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_opportunities.id"), nullable=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )


class FinancePayment(Base):
    __tablename__ = "finance_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payment_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("finance_invoices.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="wire_transfer", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )


class OperationsInventoryItem(Base):
    __tablename__ = "operations_inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    warehouse_location: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="in_stock", nullable=False)  # in_stock, low_stock, out_of_stock
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )

