from typing import Optional
from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"

    def __init__(
        self,
        id: Optional[int] = None,
        code: str = "",
        name: str = "",
        description: str = "",
        created_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            code=code,
            name=name,
            description=description,
            created_at=created_at,
            **kwargs
        )
