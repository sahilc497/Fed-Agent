from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.db.models.department_agent import DepartmentAgent
from app.db.models.user import User
from app.repositories.agent_repo import DepartmentAgentRepository
from app.repositories.user_repo import DepartmentRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.agent import DepartmentAgentOut, DepartmentAgentUpdate
from app.core.logging import get_correlation_id


class DepartmentAgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_repo = DepartmentAgentRepository(db)
        self.dept_repo = DepartmentRepository(db)
        self.audit_repo = AuditRepository(db)

    async def list_agents(self) -> List[DepartmentAgentOut]:
        agents = await self.agent_repo.list_all_agents()
        return [DepartmentAgentOut.model_validate(a) for a in agents]

    async def get_agent(self, agent_code: str) -> DepartmentAgentOut:
        agent = await self.agent_repo.get_by_code(agent_code.lower())
        if not agent:
            raise NotFoundError(f"Agent '{agent_code}' not found.")
        return DepartmentAgentOut.model_validate(agent)

    async def update_agent(
        self,
        agent_code: str,
        user: User,
        data: DepartmentAgentUpdate
    ) -> DepartmentAgentOut:
        if user.role != "admin":
            raise PermissionDeniedError("Only an administrator can update agent configurations.")

        agent = await self.agent_repo.get_by_code(agent_code.lower())
        if not agent:
            raise NotFoundError(f"Agent '{agent_code}' not found.")

        if data.name is not None:
            agent.name = data.name
        if data.description is not None:
            agent.description = data.description
        if data.system_prompt is not None:
            agent.system_prompt = data.system_prompt
        if data.is_enabled is not None:
            agent.is_enabled = data.is_enabled

        await self.db.flush()

        cid = get_correlation_id()
        await self.audit_repo.log_event(
            action="agent:updated",
            resource_type="department_agent",
            outcome="allow",
            reason=f"Administrator updated agent '{agent_code}' (enabled={agent.is_enabled})",
            correlation_id=cid,
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role,
            actor_department="admin",
            resource_id=agent_code,
            details={"is_enabled": agent.is_enabled, "agent_code": agent_code}
        )
        await self.db.commit()

        return DepartmentAgentOut.model_validate(agent)

    async def toggle_agent(self, agent_code: str, user: User, is_enabled: bool) -> DepartmentAgentOut:
        if user.role != "admin":
            raise PermissionDeniedError("Only an administrator can enable or disable agents.")

        agent = await self.agent_repo.toggle_enabled(agent_code.lower(), is_enabled)
        if not agent:
            raise NotFoundError(f"Agent '{agent_code}' not found.")

        cid = get_correlation_id()
        await self.audit_repo.log_event(
            action=f"agent:{'enabled' if is_enabled else 'disabled'}",
            resource_type="department_agent",
            outcome="allow",
            reason=f"Administrator toggled agent '{agent_code}' to {'enabled' if is_enabled else 'disabled'}",
            correlation_id=cid,
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role,
            actor_department="admin",
            resource_id=agent_code
        )
        await self.db.commit()
        return DepartmentAgentOut.model_validate(agent)
