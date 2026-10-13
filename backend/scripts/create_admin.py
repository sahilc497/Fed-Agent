import asyncio
import sys
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.db.models import User, Department


async def create_admin(email: str, password: str, full_name: str = "System Administrator"):
    async with AsyncSessionLocal() as session:
        # Check if department exists
        stmt = select(Department).where(Department.code == "finance")
        dept = (await session.execute(stmt)).scalar_one_or_none()
        if not dept:
            dept = Department(code="finance", name="Finance & Administration", description="Central Administration")
            session.add(dept)
            await session.flush()

        stmt = select(User).where(User.email == email)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            print(f"Error: User with email '{email}' already exists.")
            return

        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            department_id=dept.id,
            role="admin",
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print(f"Successfully created Administrator account: {email}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_admin.py <email> <password> [full_name]")
        sys.exit(1)

    admin_email = sys.argv[1]
    admin_pass = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "System Administrator"

    asyncio.run(create_admin(admin_email, admin_pass, name))
