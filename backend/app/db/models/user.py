from typing import Optional
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    def __init__(
        self,
        id: Optional[int] = None,
        email: str = "",
        hashed_password: str = "",
        full_name: str = "",
        department_id: int = 1,
        role: str = "department_employee",
        is_active: bool = True,
        bio: str = "",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            id=id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            department_id=department_id,
            role=role,
            is_active=bool(is_active),
            bio=bio,
            created_at=created_at,
            updated_at=updated_at,
            **kwargs
        )
