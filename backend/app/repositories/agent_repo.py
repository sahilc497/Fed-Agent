from typing import List, Optional, Any
from app.db.models.department_agent import DepartmentAgent
from app.repositories.base import BaseRepository


class DepartmentAgentRepository(BaseRepository[DepartmentAgent]):
    def __init__(self, db: Any):
        super().__init__(DepartmentAgent, db)

    async def get_by_code(self, agent_code: str) -> Optional[DepartmentAgent]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM department_agents WHERE agent_code = ? LIMIT 1;", (agent_code.lower(),))
        row = cursor.fetchone()
        return DepartmentAgent.from_row(row) if row else None

    async def get_by_department_id(self, department_id: int) -> Optional[DepartmentAgent]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM department_agents WHERE department_id = ? LIMIT 1;", (department_id,))
        row = cursor.fetchone()
        return DepartmentAgent.from_row(row) if row else None

    async def list_all_agents(self) -> List[DepartmentAgent]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM department_agents ORDER BY id;")
        rows = cursor.fetchall()
        return [DepartmentAgent.from_row(r) for r in rows]

    async def toggle_enabled(self, agent_code: str, is_enabled: bool) -> Optional[DepartmentAgent]:
        conn = self._get_conn()
        conn.execute(
            "UPDATE department_agents SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_code = ?;",
            (1 if is_enabled else 0, agent_code.lower())
        )
        return await self.get_by_code(agent_code)

    async def record_error(self, agent_code: str, error_msg: str) -> Optional[DepartmentAgent]:
        conn = self._get_conn()
        conn.execute(
            "UPDATE department_agents SET error_count = error_count + 1, last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_code = ?;",
            (error_msg, agent_code.lower())
        )
        return await self.get_by_code(agent_code)
