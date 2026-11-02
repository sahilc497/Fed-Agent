from typing import Any, Dict, Optional
from app.core.exceptions import PermissionDeniedError
from app.core.logging import get_correlation_id
from app.db.models.user import User
from app.permissions.policies import evaluate_policy
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import DepartmentRepository


class PermissionService:
    def __init__(self, db: Any):
        self.db = db
        self.audit_repo = AuditRepository(db)
        self.dept_repo = DepartmentRepository(db)

    async def check_permission(
        self,
        user: User,
        resource_type: str,
        action: str,
        resource_department_code: Optional[str] = None,
        resource_id: Optional[str] = None,
        is_sensitive: bool = False,
        extra_context: Optional[Dict[str, Any]] = None,
        raise_on_denial: bool = True
    ) -> bool:
        user_dept = await self.dept_repo.get_by_id(user.department_id)
        user_dept_code = user_dept.code if user_dept else "unknown"

        is_allowed, reason = evaluate_policy(
            user_role=user.role,
            user_department_code=user_dept_code,
            resource_department_code=resource_department_code,
            resource_type=resource_type,
            action=action,
            is_sensitive=is_sensitive,
            extra_context=extra_context
        )

        outcome = "allow" if is_allowed else "deny"
        cid = get_correlation_id()

        # Audit permission check
        await self.audit_repo.log_event(
            action=f"permission_check:{action}",
            resource_type=resource_type,
            outcome=outcome,
            reason=reason,
            correlation_id=cid,
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role,
            actor_department=user_dept_code,
            resource_id=resource_id,
            details={
                "resource_department": resource_department_code,
                "is_sensitive": is_sensitive
            }
        )

        if not is_allowed and raise_on_denial:
            raise PermissionDeniedError(f"Access denied: {reason}")

        return is_allowed
