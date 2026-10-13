from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.business_data import (
    SalesOpportunity,
    HREmployeeRecord,
    HRLeaveRecord,
    FinanceInvoice,
    FinancePayment,
    OperationsInventoryItem,
)
from app.repositories.base import BaseRepository


class SalesRepository(BaseRepository[SalesOpportunity]):
    def __init__(self, db: AsyncSession):
        super().__init__(SalesOpportunity, db)

    async def list_for_department(self, department_id: int) -> List[SalesOpportunity]:
        stmt = select(SalesOpportunity).where(SalesOpportunity.department_id == department_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_awaiting_finance_approval(self, department_id: Optional[int] = None) -> List[SalesOpportunity]:
        stmt = select(SalesOpportunity).where(
            and_(
                SalesOpportunity.needs_finance_approval == True,
                SalesOpportunity.finance_status == "pending"
            )
        )
        if department_id:
            stmt = stmt.where(SalesOpportunity.department_id == department_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class HRRepository(BaseRepository[HREmployeeRecord]):
    def __init__(self, db: AsyncSession):
        super().__init__(HREmployeeRecord, db)

    async def list_employees(self, department_id: int, include_sensitive: bool = False) -> List[HREmployeeRecord]:
        stmt = select(HREmployeeRecord).where(HREmployeeRecord.department_id == department_id)
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())
        return records

    async def get_by_code(self, employee_code: str) -> Optional[HREmployeeRecord]:
        stmt = select(HREmployeeRecord).where(HREmployeeRecord.employee_code == employee_code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class FinanceRepository(BaseRepository[FinanceInvoice]):
    def __init__(self, db: AsyncSession):
        super().__init__(FinanceInvoice, db)

    async def list_invoices(self, department_id: int, status: Optional[str] = None) -> List[FinanceInvoice]:
        stmt = select(FinanceInvoice).where(FinanceInvoice.department_id == department_id)
        if status:
            stmt = stmt.where(FinanceInvoice.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_overdue_invoices(self, department_id: int) -> List[FinanceInvoice]:
        stmt = select(FinanceInvoice).where(
            and_(
                FinanceInvoice.department_id == department_id,
                FinanceInvoice.status == "overdue"
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_invoice_number(self, invoice_number: str) -> Optional[FinanceInvoice]:
        stmt = select(FinanceInvoice).where(FinanceInvoice.invoice_number == invoice_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class OperationsRepository(BaseRepository[OperationsInventoryItem]):
    def __init__(self, db: AsyncSession):
        super().__init__(OperationsInventoryItem, db)

    async def list_items(self, department_id: int, status: Optional[str] = None) -> List[OperationsInventoryItem]:
        stmt = select(OperationsInventoryItem).where(OperationsInventoryItem.department_id == department_id)
        if status:
            stmt = stmt.where(OperationsInventoryItem.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_sku(self, sku: str) -> Optional[OperationsInventoryItem]:
        stmt = select(OperationsInventoryItem).where(OperationsInventoryItem.sku == sku)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

