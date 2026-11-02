from typing import Optional
from app.db.base import Base


class DepartmentAgent(Base):
    __tablename__ = "department_agents"

    def __init__(
        self,
        id: Optional[int] = None,
        department_id: int = 1,
        agent_code: str = "",
        name: str = "",
        description: str = "",
        system_prompt: str = "",
        is_enabled: bool = True,
        error_count: int = 0,
        last_error: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            department_id=department_id,
            agent_code=agent_code,
            name=name,
            description=description,
            system_prompt=system_prompt,
            is_enabled=bool(is_enabled),
            error_count=int(error_count or 0),
            last_error=last_error,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs
        )
