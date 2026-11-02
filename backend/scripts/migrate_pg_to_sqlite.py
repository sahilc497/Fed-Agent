import os
import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.db.sqlite import create_connection
from app.db.schema import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pg_to_sqlite_migration")


def check_and_migrate():
    logger.info("Initializing destination SQLite schema...")
    init_db()

    pg_url = getattr(settings, "SYNC_DATABASE_URL", None) or "postgresql://postgres:postgres@localhost:5432/federated_mesh_dev"
    logger.info(f"Checking connectivity to source PostgreSQL database: {pg_url}")

    try:
        import psycopg2
        # Try connecting with short timeout
        conn_pg = psycopg2.connect(pg_url, connect_timeout=3)
        cursor_pg = conn_pg.cursor()
        logger.info("Connected to source PostgreSQL database successfully. Starting table extraction...")

        sqlite_conn = create_connection()
        # Migrate departments
        cursor_pg.execute("SELECT id, code, name, description FROM departments;")
        depts = cursor_pg.fetchall()
        for d in depts:
            sqlite_conn.execute(
                "INSERT INTO departments (id, code, name, description) VALUES (?, ?, ?, ?) ON CONFLICT(code) DO NOTHING;",
                d
            )
        logger.info(f"Migrated {len(depts)} departments from PostgreSQL.")

        # Migrate users
        cursor_pg.execute("SELECT id, email, hashed_password, full_name, role, department_id, is_active FROM users;")
        users = cursor_pg.fetchall()
        for u in users:
            sqlite_conn.execute(
                "INSERT INTO users (id, email, hashed_password, full_name, role, department_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(email) DO NOTHING;",
                u
            )
        logger.info(f"Migrated {len(users)} users from PostgreSQL.")

        sqlite_conn.commit()
        sqlite_conn.close()
        cursor_pg.close()
        conn_pg.close()
        logger.info("PostgreSQL migration completed successfully.")
        return True
    except Exception as exc:
        logger.warning(
            f"Source PostgreSQL database was not accessible ({exc}). "
            "Safe fallback: SQLite is already initialized with structured synthetic datasets. "
            "No data was lost or overwritten."
        )
        return False


if __name__ == "__main__":
    check_and_migrate()
