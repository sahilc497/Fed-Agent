import pytest
from app.permissions.policies import evaluate_policy, Role, Action, ResourceType


def test_deny_by_default():
    # Random unmapped action and resource
    allowed, reason = evaluate_policy(
        user_role="unknown_role",
        user_department_code="unknown_dept",
        resource_department_code="other_dept",
        resource_type="secret_key",
        action="read"
    )
    assert not allowed
    assert "denied" in reason.lower() or "deny" in reason.lower()


def test_audit_log_immutable_for_admin():
    # Admin cannot delete or update audit logs
    allowed, reason = evaluate_policy(
        user_role=Role.ADMIN.value,
        user_department_code="finance",
        resource_department_code="finance",
        resource_type=ResourceType.AUDIT_LOG.value,
        action=Action.DELETE.value
    )
    assert not allowed
    assert "immutable" in reason.lower()


def test_sensitive_salary_policy():
    # Regular HR employee cannot view sensitive salary
    emp_allowed, _ = evaluate_policy(
        user_role=Role.DEPARTMENT_EMPLOYEE.value,
        user_department_code="hr",
        resource_department_code="hr",
        resource_type=ResourceType.SALARY.value,
        action=Action.READ.value,
        is_sensitive=True
    )
    assert not emp_allowed

    # HR Manager CAN view sensitive salary
    mgr_allowed, _ = evaluate_policy(
        user_role=Role.DEPARTMENT_MANAGER.value,
        user_department_code="hr",
        resource_department_code="hr",
        resource_type=ResourceType.SALARY.value,
        action=Action.READ.value,
        is_sensitive=True
    )
    assert mgr_allowed
