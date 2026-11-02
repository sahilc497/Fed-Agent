from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db
from app.db.models.user import User
from app.services.user_service import UserService
from app.repositories.user_repo import DepartmentRepository
from app.repositories.business_repo import (
    SalesRepository,
    HRRepository,
    FinanceRepository,
    OperationsRepository
)
from app.schemas.department import DepartmentOut, DepartmentSummary
from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=List[DepartmentOut])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """Lists registered enterprise departments."""
    user_service = UserService(db)
    return await user_service.list_departments()


@router.get("/me/summary", response_model=DepartmentSummary)
async def get_my_department_summary(
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
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
    db: Any = Depends(get_db)
):
    """
    Returns authorized business records for the department.
    Enforces strict zero-trust boundary:
    Non-admin users can only view their own department's records.
    Sensitive HR fields (such as salary) are masked for unauthorized callers.
    """
    code = department_code.lower().strip()
    dept_repo = DepartmentRepository(db)
    dept = await dept_repo.get_by_code(code)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department '{department_code}' not found.")

    # Cross-department check: only admin or members of this department can access
    is_admin = current_user.role == "admin"
    if not is_admin and current_user.department_id != dept.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Direct access to {dept.name} records is prohibited by department isolation policy."
        )

    if code == "sales":
        sales_repo = SalesRepository(db)
        records = await sales_repo.list_for_department(dept.id)
        return [
            {
                "id": r.id,
                "title": r.title,
                "client_name": r.client_name,
                "deal_value": r.deal_value,
                "stage": r.stage,
                "needs_finance_approval": bool(r.needs_finance_approval),
                "finance_status": r.finance_status,
                "created_at": str(r.created_at) if r.created_at else None
            }
            for r in records
        ]

    elif code == "hr":
        hr_repo = HRRepository(db)
        can_view_salary = current_user.role == "admin" or (current_user.role == "department_manager" and current_user.department_id == dept.id)
        records = await hr_repo.list_employees(dept.id, include_sensitive=can_view_salary)
        return [
            {
                "id": r.id,
                "employee_code": r.employee_code,
                "full_name": r.full_name,
                "position": r.position,
                "leave_balance": r.leave_balance,
                "salary": r.salary if can_view_salary else None,
                "performance_rating": r.performance_rating,
                "is_sensitive": bool(r.is_sensitive),
                "created_at": str(r.created_at) if r.created_at else None
            }
            for r in records
        ]

    elif code == "finance":
        fin_repo = FinanceRepository(db)
        records = await fin_repo.list_invoices(dept.id)
        return [
            {
                "id": r.id,
                "invoice_number": r.invoice_number,
                "client_name": r.client_name,
                "amount": r.amount,
                "status": r.status,
                "due_date": str(r.due_date) if r.due_date else None,
                "created_at": str(r.created_at) if r.created_at else None
            }
            for r in records
        ]

    elif code == "operations":
        ops_repo = OperationsRepository(db)
        records = await ops_repo.list_items(dept.id)
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
                "created_at": str(r.created_at) if r.created_at else None
            }
            for r in records
        ]

    return []
