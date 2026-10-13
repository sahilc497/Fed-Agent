import os
import sys
import asyncio

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.base import Base
from app.db.session import async_engine
import app.db.models  # Register all models


async def init_schema():
    print("Creating all tables in PostgreSQL database...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema successfully synchronized!")


if __name__ == "__main__":
    asyncio.run(init_schema())
