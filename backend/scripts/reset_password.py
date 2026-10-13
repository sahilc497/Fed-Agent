import os
import sys
import asyncio
from sqlalchemy import select

# Ensure backend root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.db.models.user import User


async def reset_password(email: str, new_password: str):
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            print(f"Error: User '{email}' not found.")
            return False

        user.hashed_password = hash_password(new_password)
        await session.commit()
        # Never print real password
        print(f"Success: Password for '{email}' has been reset securely using Argon2id.")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/reset_password.py <email> <new_password>")
        sys.exit(1)

    user_email = sys.argv[1]
    pwd = sys.argv[2]
    asyncio.run(reset_password(user_email, pwd))
