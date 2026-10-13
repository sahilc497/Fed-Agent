from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.department_agent import DepartmentAgent
from app.repositories.base import BaseRepository


class DepartmentAgentRepository(BaseRepository[DepartmentAgent]):
    def __init__(self, db: AsyncSession):
        super().__init__(DepartmentAgent, db)

    async def get_by_code(self, agent_code: str) -> Optional[DepartmentAgent]:
        stmt = select(DepartmentAgent).where(DepartmentAgent.agent_code == agent_code.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_department_id(self, department_id: int) -> Optional[DepartmentAgent]:
        stmt = select(DepartmentAgent).where(DepartmentAgent.department_id == department_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all_agents(self) -> List[DepartmentAgent]:
        stmt = select(DepartmentAgent).order_by(DepartmentAgent.id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def toggle_enabled(self, agent_code: str, is_enabled: bool) -> Optional[DepartmentAgent]:
        agent = await self.get_by_code(agent_code)
        if agent:
            agent.is_enabled = is_enabled
            await self.db.flush()
        return agent

    async def record_error(self, agent_code: str, error_msg: str) -> Optional[DepartmentAgent]:
        agent = await self.get_by_code(agent_code)
        if agent:
            agent.error_count += 1
            agent.last_error = error_msg
            await self.db.flush()
        return agent
