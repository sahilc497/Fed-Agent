from enum import Enum
from typing import Any, Dict, Optional


class Role(str, Enum):
    ADMIN = "admin"
    DEPARTMENT_MANAGER = "department_manager"
    DEPARTMENT_EMPLOYEE = "department_employee"
    AUDITOR = "auditor"


class Action(str, Enum):
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    EXECUTE = "execute"
    FEDERATED_QUERY = "federated_query"


class ResourceType(str, Enum):
    OPPORTUNITY = "sales_opportunity"
    EMPLOYEE_RECORD = "hr_employee_record"
    SALARY = "hr_salary"
    INVOICE = "finance_invoice"
    PAYMENT = "finance_payment"
    DOCUMENT = "document"
    APPROVAL = "approval"
    AUDIT_LOG = "audit_log"
    USER = "user"
    DEPARTMENT = "department"


# Default base policy matrix (deny by default)
# Returns (is_allowed: bool, reason: str)
def evaluate_policy(
    user_role: str,
    user_department_code: str,
    resource_department_code: Optional[str],
    resource_type: str,
    action: str,
    is_sensitive: bool = False,
    extra_context: Optional[Dict[str, Any]] = None
) -> tuple[bool, str]:
    extra_context = extra_context or {}

    # 1. Admin has broad administrative management, but audit is immutable
    if user_role == Role.ADMIN.value:
        if resource_type == ResourceType.AUDIT_LOG.value and action in [Action.WRITE.value, Action.UPDATE.value, Action.DELETE.value]:
            return False, "Audit logs are strictly immutable and cannot be modified even by admin."
        return True, "Granted by Administrator role."

    # 2. Auditor role: Read-only access to audit logs and department summaries
    if user_role == Role.AUDITOR.value:
        if action == Action.READ.value and resource_type in [ResourceType.AUDIT_LOG.value, ResourceType.DEPARTMENT.value]:
            return True, "Granted read-only access for Auditor."
        return False, "Auditor role has read-only access restricted to audit logs and system summaries."

    # 3. Audit log write/update/delete blocked for ordinary employees and managers
    if resource_type == ResourceType.AUDIT_LOG.value:
        return False, "Direct user access to write or modify audit logs is prohibited."

    # 4. Department isolation: User cannot directly access another department's resources
    if resource_department_code and resource_department_code != user_department_code:
        # Cross-department requests must go through the Federation Gateway
        return False, f"Cross-department direct access denied. Must route through Federation Gateway. (Caller: {user_department_code}, Target: {resource_department_code})"

    # 5. Sensitive HR Data (Salaries, performance ratings):
    # Only HR Managers can view salaries; HR Employees cannot see other employees' salaries.
    if resource_type == ResourceType.SALARY.value or (resource_type == ResourceType.EMPLOYEE_RECORD.value and is_sensitive):
        if user_department_code == "hr" and user_role == Role.DEPARTMENT_MANAGER.value:
            return True, "HR Department Manager permitted access to sensitive HR compensation records."
        return False, "Access denied to confidential salary and compensation records."

    # 6. Approvals: Only Managers can approve; Employees cannot approve sensitive actions
    if resource_type == ResourceType.APPROVAL.value and action == Action.APPROVE.value:
        if user_role == Role.DEPARTMENT_MANAGER.value:
            return True, "Department Manager authorized to decide approval requests."
        return False, "Only Department Managers and authorized personnel can approve requests."

    # 7. Same department operations:
    if resource_department_code == user_department_code or resource_department_code is None:
        if action in [Action.READ.value, Action.FEDERATED_QUERY.value]:
            return True, f"Authorized {action} access within own department ({user_department_code})."
        if action in [Action.WRITE.value, Action.UPDATE.value]:
            return True, f"Authorized write access within own department ({user_department_code})."
        if action == Action.DELETE.value:
            if user_role == Role.DEPARTMENT_MANAGER.value:
                return True, "Department Manager authorized to delete department resources."
            return False, "Department Employees cannot delete department records."

    return False, "Deny by default: No matching policy permits this operation."
