from typing import List, Optional, Any
from app.db.models.business_data import (
    SalesCustomer,
    SalesOpportunity,
    HREmployeeRecord,
    HRLeaveRecord,
    FinanceVendor,
    FinanceInvoice,
    FinancePayment,
    OperationsSupplier,
    OperationsInventoryItem,
    OperationsPurchaseOrder,
)
from app.repositories.base import BaseRepository


class SalesRepository(BaseRepository[SalesOpportunity]):
    def __init__(self, db: Any):
        super().__init__(SalesOpportunity, db)

    async def list_for_department(self, department_id: int) -> List[SalesOpportunity]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM sales_opportunities WHERE department_id = ? ORDER BY id;", (department_id,))
        rows = cursor.fetchall()
        return [SalesOpportunity.from_row(r) for r in rows]

    async def list_awaiting_finance_approval(self, department_id: Optional[int] = None) -> List[SalesOpportunity]:
        conn = self._get_conn()
        query = "SELECT * FROM sales_opportunities WHERE needs_finance_approval = 1 AND finance_status = 'pending'"
        params = []
        if department_id is not None:
            query += " AND department_id = ?"
            params.append(department_id)
        query += " ORDER BY id;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [SalesOpportunity.from_row(r) for r in rows]

    async def list_customers(self) -> List[SalesCustomer]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM sales_customers ORDER BY id;")
        rows = cursor.fetchall()
        return [SalesCustomer.from_row(r) for r in rows]


class HRRepository(BaseRepository[HREmployeeRecord]):
    def __init__(self, db: Any):
        super().__init__(HREmployeeRecord, db)

    async def list_employees(self, department_id: int, include_sensitive: bool = False) -> List[HREmployeeRecord]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM hr_employees WHERE department_id = ? ORDER BY id;", (department_id,))
        rows = cursor.fetchall()
        records = [HREmployeeRecord.from_row(r) for r in rows]
        if not include_sensitive:
            for rec in records:
                rec.salary = 0.0  # Mask sensitive salary
        return records

    async def get_by_code(self, employee_code: str) -> Optional[HREmployeeRecord]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM hr_employees WHERE employee_code = ? LIMIT 1;", (employee_code,))
        row = cursor.fetchone()
        return HREmployeeRecord.from_row(row) if row else None

    async def list_leaves(self, employee_id: Optional[int] = None) -> List[HRLeaveRecord]:
        conn = self._get_conn()
        query = "SELECT * FROM hr_leaves"
        params = []
        if employee_id is not None:
            query += " WHERE employee_id = ?"
            params.append(employee_id)
        query += " ORDER BY id;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [HRLeaveRecord.from_row(r) for r in rows]


class FinanceRepository(BaseRepository[FinanceInvoice]):
    def __init__(self, db: Any):
        super().__init__(FinanceInvoice, db)

    async def list_invoices(self, department_id: int, status: Optional[str] = None) -> List[FinanceInvoice]:
        conn = self._get_conn()
        query = "SELECT * FROM finance_invoices WHERE department_id = ?"
        params = [department_id]
        if status:
            query += " AND status = ?"
            params.append(status.lower())
        query += " ORDER BY id;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [FinanceInvoice.from_row(r) for r in rows]

    async def list_overdue_invoices(self, department_id: int) -> List[FinanceInvoice]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM finance_invoices WHERE department_id = ? AND status = 'overdue' ORDER BY id;",
            (department_id,)
        )
        rows = cursor.fetchall()
        return [FinanceInvoice.from_row(r) for r in rows]

    async def get_by_invoice_number(self, invoice_number: str) -> Optional[FinanceInvoice]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM finance_invoices WHERE invoice_number = ? LIMIT 1;", (invoice_number,))
        row = cursor.fetchone()
        return FinanceInvoice.from_row(row) if row else None

    async def list_vendors(self) -> List[FinanceVendor]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM finance_vendors ORDER BY id;")
        rows = cursor.fetchall()
        return [FinanceVendor.from_row(r) for r in rows]


class OperationsRepository(BaseRepository[OperationsInventoryItem]):
    def __init__(self, db: Any):
        super().__init__(OperationsInventoryItem, db)

    async def list_items(self, department_id: int, status: Optional[str] = None) -> List[OperationsInventoryItem]:
        conn = self._get_conn()
        query = "SELECT * FROM operations_inventory WHERE department_id = ?"
        params = [department_id]
        if status:
            query += " AND status = ?"
            params.append(status.lower())
        query += " ORDER BY id;"
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [OperationsInventoryItem.from_row(r) for r in rows]

    async def get_by_sku(self, sku: str) -> Optional[OperationsInventoryItem]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM operations_inventory WHERE sku = ? LIMIT 1;", (sku,))
        row = cursor.fetchone()
        return OperationsInventoryItem.from_row(row) if row else None

    async def list_suppliers(self) -> List[OperationsSupplier]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM operations_suppliers ORDER BY id;")
        rows = cursor.fetchall()
        return [OperationsSupplier.from_row(r) for r in rows]
