from typing import List, Optional, Any
from app.core.security import hash_password
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.db.models.user import User
from app.repositories.user_repo import UserRepository, DepartmentRepository
from app.schemas.user import UserCreate, UserOut
from app.schemas.department import DepartmentOut, DepartmentSummary


class UserService:
    def __init__(self, db: Any):
        self.db = db
        self.user_repo = UserRepository(db)
        self.dept_repo = DepartmentRepository(db)

    def _get_conn(self):
        if hasattr(self.db, "conn"):
            return self.db.conn
        return self.db

    async def list_departments(self) -> List[DepartmentOut]:
        depts = await self.dept_repo.list_all()
        return [DepartmentOut.model_validate(d) for d in depts]

    async def get_department_summary(self, user: User) -> DepartmentSummary:
        dept = await self.dept_repo.get_by_id(user.department_id)
        if not dept:
            raise NotFoundError("User department not found.")

        conn = self._get_conn()
        # Count users in department
        row = conn.execute("SELECT COUNT(*) FROM users WHERE department_id = ?;", (dept.id,)).fetchone()
        user_count = row[0] if row else 0

        # Count documents in department
        row = conn.execute("SELECT COUNT(*) FROM documents WHERE department_id = ?;", (dept.id,)).fetchone()
        doc_count = row[0] if row else 0

        # Department specific metrics
        metrics = {}
        if dept.code == "sales":
            row = conn.execute("SELECT COUNT(*) FROM sales_opportunities WHERE department_id = ?;", (dept.id,)).fetchone()
            metrics["total_opportunities"] = row[0] if row else 0
        elif dept.code == "hr":
            row = conn.execute("SELECT COUNT(*) FROM hr_employees WHERE department_id = ?;", (dept.id,)).fetchone()
            metrics["employee_count"] = row[0] if row else 0
        elif dept.code == "finance":
            row = conn.execute("SELECT COUNT(*) FROM finance_invoices WHERE department_id = ?;", (dept.id,)).fetchone()
            metrics["total_invoices"] = row[0] if row else 0
        elif dept.code == "operations":
            row = conn.execute("SELECT COUNT(*) FROM operations_inventory WHERE department_id = ?;", (dept.id,)).fetchone()
            metrics["total_inventory_items"] = row[0] if row else 0

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
            is_active=data.is_active,
            bio=data.bio or ""
        )
        created = await self.user_repo.create(user)
        return UserOut.model_validate(created)
