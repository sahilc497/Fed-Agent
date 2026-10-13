from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import PermissionDeniedError
from app.db.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import DepartmentRepository
from app.schemas.audit import AuditLogOut, AuditFilterParams


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditRepository(db)
        self.dept_repo = DepartmentRepository(db)

    async def get_audit_logs(self, user: User, params: AuditFilterParams) -> List[AuditLogOut]:
        user_dept = await self.dept_repo.get_by_id(user.department_id)
        user_dept_code = user_dept.code if user_dept else "unknown"

        # Access check
        if user.role not in ["admin", "auditor", "department_manager"]:
            raise PermissionDeniedError("Audit log access is restricted to Administrators, Auditors, and Department Managers.")

        # If department manager, scope strictly to their department
        scoped_dept = params.department
        if user.role == "department_manager":
            scoped_dept = user_dept_code

        logs = await self.audit_repo.list_audit_logs(
            department=scoped_dept,
            action=params.action,
            outcome=params.outcome,
            skip=params.offset,
            limit=params.limit
        )
        return [AuditLogOut.model_validate(log) for log in logs]
