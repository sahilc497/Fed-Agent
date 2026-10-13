from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.db.models.user import User
from app.db.models.department import Department
from app.db.models.document import Document
from app.db.models.business_data import SalesOpportunity, HREmployeeRecord, FinanceInvoice, OperationsInventoryItem
from app.repositories.user_repo import UserRepository, DepartmentRepository
from app.schemas.user import UserCreate, UserOut
from app.schemas.department import DepartmentOut, DepartmentSummary


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.dept_repo = DepartmentRepository(db)

    async def list_departments(self) -> List[DepartmentOut]:
        depts = await self.dept_repo.list_all()
        return [DepartmentOut.model_validate(d) for d in depts]

    async def get_department_summary(self, user: User) -> DepartmentSummary:
        dept = await self.dept_repo.get_by_id(user.department_id)
        if not dept:
            raise NotFoundError("User department not found.")

        # Count users in department
        u_count_res = await self.db.execute(
            select(func.count(User.id)).where(User.department_id == dept.id)
        )
        user_count = u_count_res.scalar() or 0

        # Count documents in department
        d_count_res = await self.db.execute(
            select(func.count(Document.id)).where(Document.department_id == dept.id)
        )
        doc_count = d_count_res.scalar() or 0

        # Department specific metrics
        metrics = {}
        if dept.code == "sales":
            opp_res = await self.db.execute(
                select(func.count(SalesOpportunity.id)).where(SalesOpportunity.department_id == dept.id)
            )
            metrics["total_opportunities"] = opp_res.scalar() or 0
        elif dept.code == "hr":
            emp_res = await self.db.execute(
                select(func.count(HREmployeeRecord.id)).where(HREmployeeRecord.department_id == dept.id)
            )
            metrics["employee_count"] = emp_res.scalar() or 0
        elif dept.code == "finance":
            inv_res = await self.db.execute(
                select(func.count(FinanceInvoice.id)).where(FinanceInvoice.department_id == dept.id)
            )
            metrics["total_invoices"] = inv_res.scalar() or 0
        elif dept.code == "operations":
            ops_res = await self.db.execute(
                select(func.count(OperationsInventoryItem.id)).where(OperationsInventoryItem.department_id == dept.id)
            )
            metrics["total_inventory_items"] = ops_res.scalar() or 0


        return DepartmentSummary(
            department_id=dept.id,
            department_name=dept.name,
            department_code=dept.code,
            user_count=user_count,
            authorized_document_count=doc_count,
            metrics=metrics
        )

    async def create_user(self, creator: User, data: UserCreate) -> UserOut:
        if creator.role != "admin":
            raise PermissionDeniedError("Only an administrator can create users.")

        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError(f"User with email {data.email} already exists.")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            department_id=data.department_id,
            role=data.role,
            is_active=data.is_active
        )
        created = await self.user_repo.create(user)
        return UserOut.model_validate(created)
