from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.schemas.chat import EvidenceReference


class AgentTaskResult:
    def __init__(
        self,
        success: bool,
        department: str,
        content: str,
        evidence: List[EvidenceReference],
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.department = department
        self.content = content
        self.evidence = evidence
        self.metadata = metadata or {}
        self.error = error


class BaseAgent(ABC):
    def __init__(self, department_code: str, db: AsyncSession):
        self.department_code = department_code
        self.db = db

    @abstractmethod
    async def execute_task(
        self,
        user: User,
        task_query: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentTaskResult:
        """Executes a department-scoped agent task."""
        pass
