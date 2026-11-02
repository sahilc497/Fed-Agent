from typing import Optional, List, Any
from app.db.models.user import User
from app.db.models.department import Department
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Any):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM users WHERE email = ? LIMIT 1;", (email,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None

    async def get_by_department(self, department_id: int) -> List[User]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM users WHERE department_id = ? ORDER BY id;", (department_id,))
        rows = cursor.fetchall()
        return [User.from_row(r) for r in rows]

    async def update_profile(self, user_id: int, full_name: Optional[str] = None, bio: Optional[str] = None) -> Optional[User]:
        conn = self._get_conn()
        updates = []
        params = []
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        if not updates:
            return await self.get_by_id(user_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?;", tuple(params))
        return await self.get_by_id(user_id)

    async def update_admin(
        self,
        user_id: int,
        role: Optional[str] = None,
        department_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        full_name: Optional[str] = None
    ) -> Optional[User]:
        conn = self._get_conn()
        updates = []
        params = []
        if role is not None:
            updates.append("role = ?")
            params.append(role)
        if department_id is not None:
            updates.append("department_id = ?")
            params.append(department_id)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)
        if not updates:
            return await self.get_by_id(user_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?;", tuple(params))
        return await self.get_by_id(user_id)


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Any):
        super().__init__(Department, db)

    async def get_by_code(self, code: str) -> Optional[Department]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM departments WHERE code = ? LIMIT 1;", (code.lower(),))
        row = cursor.fetchone()
        return Department.from_row(row) if row else None
