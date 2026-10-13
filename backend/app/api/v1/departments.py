from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import User
from app.services.user_service import UserService
from app.schemas.department import DepartmentOut, DepartmentSummary
from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=List[DepartmentOut])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists registered enterprise departments."""
    user_service = UserService(db)
    return await user_service.list_departments()


@router.get("/me/summary", response_model=DepartmentSummary)
async def get_my_department_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns department summary restricted to the caller's permitted scope."""
    user_service = UserService(db)
    try:
        return await user_service.get_department_summary(current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{department_code}/records")
async def get_department_records(
    department_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns authorized business records for the department.
    Enforces strict zero-trust boundary:
    Non-admin/non-auditor users can only view their own department's records.
    Sensitive HR fields (such as salary) are masked for unauthorized callers.
    """
    from sqlalchemy import select
    from app.db.models.department import Department
    from app.db.models.business_data import SalesOpportunity, HREmployeeRecord, FinanceInvoice, OperationsInventoryItem

    code = department_code.lower().strip()
    dept = (await db.execute(select(Department).where(Department.code == code))).scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department '{department_code}' not found.")

    # Cross-department check: only admin or auditor or members of this department can access
    is_admin_or_auditor = current_user.role in ["admin", "auditor"]
    if not is_admin_or_auditor and current_user.department_id != dept.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Direct access to {dept.name} records is prohibited by department isolation policy."
        )

    if code == "sales":
        res = await db.execute(select(SalesOpportunity).where(SalesOpportunity.department_id == dept.id).order_by(SalesOpportunity.id))
        records = res.scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "client_name": r.client_name,
                "deal_value": r.deal_value,
                "stage": r.stage,
                "needs_finance_approval": r.needs_finance_approval,
                "finance_status": r.finance_status,
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]

    elif code == "hr":
        res = await db.execute(select(HREmployeeRecord).where(HREmployeeRecord.department_id == dept.id).order_by(HREmployeeRecord.id))
        records = res.scalars().all()
        can_view_salary = current_user.role in ["admin"] or (current_user.role == "department_manager" and current_user.department_id == dept.id)
        return [
            {
                "id": r.id,
                "employee_code": r.employee_code,
                "full_name": r.full_name,
                "position": r.position,
                "leave_balance": r.leave_balance,
                "salary": r.salary if can_view_salary else None,
                "performance_rating": r.performance_rating,
                "is_sensitive": r.is_sensitive,
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]

    elif code == "finance":
        res = await db.execute(select(FinanceInvoice).where(FinanceInvoice.department_id == dept.id).order_by(FinanceInvoice.id))
        records = res.scalars().all()
        return [
            {
                "id": r.id,
                "invoice_number": r.invoice_number,
                "client_name": r.client_name,
                "amount": r.amount,
                "status": r.status,
                "due_date": r.due_date.isoformat(),
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]

    elif code == "operations":
        res = await db.execute(select(OperationsInventoryItem).where(OperationsInventoryItem.department_id == dept.id).order_by(OperationsInventoryItem.id))
        records = res.scalars().all()
        return [
            {
                "id": r.id,
                "sku": r.sku,
                "item_name": r.item_name,
                "category": r.category,
                "quantity_on_hand": r.quantity_on_hand,
                "reorder_threshold": r.reorder_threshold,
                "warehouse_location": r.warehouse_location,
                "status": r.status,
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]

    return []

