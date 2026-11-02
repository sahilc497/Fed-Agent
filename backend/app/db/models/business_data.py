from typing import Optional
from app.db.base import Base


class SalesCustomer(Base):
    __tablename__ = "sales_customers"

    def __init__(
        self,
        id: Optional[int] = None,
        customer_code: str = "",
        company_name: str = "",
        industry: str = "",
        contact_name: str = "",
        contact_email: str = "",
        status: str = "active",
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            customer_code=customer_code,
            company_name=company_name,
            industry=industry,
            contact_name=contact_name,
            contact_email=contact_email,
            status=status,
            created_at=created_at,
            **kwargs
        )


class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"

    def __init__(
        self,
        id: Optional[int] = None,
        customer_id: Optional[int] = None,
        title: str = "",
        client_name: str = "",
        deal_value: float = 0.0,
        stage: str = "lead",
        probability: float = 0.5,
        lead_source: str = "direct",
        needs_finance_approval: bool = False,
        finance_status: str = "none",
        owner_id: int = 1,
        department_id: int = 1,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            customer_id=customer_id,
            title=title,
            client_name=client_name,
            deal_value=float(deal_value or 0.0),
            stage=stage,
            probability=float(probability or 0.5),
            lead_source=lead_source,
            needs_finance_approval=bool(needs_finance_approval),
            finance_status=finance_status,
            owner_id=owner_id,
            department_id=department_id,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs
        )


class HREmployeeRecord(Base):
    __tablename__ = "hr_employees"

    def __init__(
        self,
        id: Optional[int] = None,
        employee_code: str = "",
        full_name: str = "",
        position: str = "",
        department_id: int = 2,
        leave_balance: int = 20,
        salary: float = 0.0,
        performance_rating: str = "Satisfactory",
        joining_date: str = "",
        employment_status: str = "active",
        is_sensitive: bool = True,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            employee_code=employee_code,
            full_name=full_name,
            position=position,
            department_id=department_id,
            leave_balance=int(leave_balance or 0),
            salary=float(salary or 0.0),
            performance_rating=performance_rating,
            joining_date=joining_date,
            employment_status=employment_status,
            is_sensitive=bool(is_sensitive),
            created_at=created_at,
            updated_at=updated_at,
            **kwargs
        )


HREmployee = HREmployeeRecord


class HRLeaveRecord(Base):
    __tablename__ = "hr_leaves"

    def __init__(
        self,
        id: Optional[int] = None,
        employee_id: int = 1,
        leave_type: str = "annual",
        days: int = 1,
        status: str = "approved",
        start_date: str = "",
        end_date: str = "",
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            employee_id=employee_id,
            leave_type=leave_type,
            days=int(days or 1),
            status=status,
            start_date=start_date,
            end_date=end_date,
            created_at=created_at,
            **kwargs
        )


HRLeave = HRLeaveRecord


class FinanceVendor(Base):
    __tablename__ = "finance_vendors"

    def __init__(
        self,
        id: Optional[int] = None,
        vendor_code: str = "",
        name: str = "",
        category: str = "",
        contact_email: str = "",
        status: str = "active",
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            vendor_code=vendor_code,
            name=name,
            category=category,
            contact_email=contact_email,
            status=status,
            created_at=created_at,
            **kwargs
        )


class FinanceInvoice(Base):
    __tablename__ = "finance_invoices"

    def __init__(
        self,
        id: Optional[int] = None,
        vendor_id: Optional[int] = None,
        invoice_number: str = "",
        client_name: str = "",
        amount: float = 0.0,
        status: str = "sent",
        due_date: Optional[str] = None,
        related_opportunity_id: Optional[int] = None,
        department_id: int = 3,
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            vendor_id=vendor_id,
            invoice_number=invoice_number,
            client_name=client_name,
            amount=float(amount or 0.0),
            status=status,
            due_date=due_date,
            related_opportunity_id=related_opportunity_id,
            department_id=department_id,
            created_at=created_at,
            **kwargs
        )


class FinancePayment(Base):
    __tablename__ = "finance_payments"

    def __init__(
        self,
        id: Optional[int] = None,
        invoice_id: int = 1,
        payment_reference: str = "",
        amount: float = 0.0,
        payment_method: str = "wire_transfer",
        status: str = "completed",
        department_id: int = 3,
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            invoice_id=invoice_id,
            payment_reference=payment_reference,
            amount=float(amount or 0.0),
            payment_method=payment_method,
            status=status,
            department_id=department_id,
            created_at=created_at,
            **kwargs
        )


class FinanceBudget(Base):
    __tablename__ = "finance_budgets"

    def __init__(
        self,
        id: Optional[int] = None,
        department_id: int = 3,
        fiscal_year: str = "2026",
        allocated_amount: float = 0.0,
        spent_amount: float = 0.0,
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            department_id=department_id,
            fiscal_year=fiscal_year,
            allocated_amount=float(allocated_amount or 0.0),
            spent_amount=float(spent_amount or 0.0),
            created_at=created_at,
            **kwargs
        )


class OperationsSupplier(Base):
    __tablename__ = "operations_suppliers"

    def __init__(
        self,
        id: Optional[int] = None,
        supplier_code: str = "",
        name: str = "",
        contact_email: str = "",
        status: str = "active",
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            supplier_code=supplier_code,
            name=name,
            contact_email=contact_email,
            status=status,
            created_at=created_at,
            **kwargs
        )


class OperationsInventoryItem(Base):
    __tablename__ = "operations_inventory"

    def __init__(
        self,
        id: Optional[int] = None,
        sku: str = "",
        item_name: str = "",
        category: str = "",
        quantity_on_hand: int = 0,
        reserved_quantity: int = 0,
        reorder_threshold: int = 10,
        warehouse_location: str = "",
        supplier_id: Optional[int] = None,
        status: str = "in_stock",
        department_id: int = 4,
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            sku=sku,
            item_name=item_name,
            category=category,
            quantity_on_hand=int(quantity_on_hand or 0),
            reserved_quantity=int(reserved_quantity or 0),
            reorder_threshold=int(reorder_threshold or 10),
            warehouse_location=warehouse_location,
            supplier_id=supplier_id,
            status=status,
            department_id=department_id,
            created_at=created_at,
            **kwargs
        )


OperationsInventory = OperationsInventoryItem


class OperationsPurchaseOrder(Base):
    __tablename__ = "operations_purchase_orders"

    def __init__(
        self,
        id: Optional[int] = None,
        po_number: str = "",
        supplier_id: int = 1,
        sku: str = "",
        quantity: int = 1,
        status: str = "ordered",
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            po_number=po_number,
            supplier_id=supplier_id,
            sku=sku,
            quantity=int(quantity or 1),
            status=status,
            created_at=created_at,
            **kwargs
        )
