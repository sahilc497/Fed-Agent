import logging
import sqlite3
from typing import Optional, List, Tuple, Callable
from app.db.sqlite import create_connection
from app.db.schema import init_db, CURRENT_SCHEMA_VERSION

logger = logging.getLogger("federated_mesh.db.migrations")


# List of incremental version migrations: (version, description, migration_fn or sql)
MIGRATIONS: List[Tuple[int, str, Optional[str]]] = [
    (1, "Initial SQLite schema for Federated Agentic Mesh", None),
]


def run_migrations(db_path: Optional[str] = None) -> int:
    """
    Executes versioned migrations idempotently without destroying existing data.
    """
    # Step 1: Ensure base schema is present
    init_db(db_path)
    
    conn = create_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM _schema_version;")
        row = cursor.fetchone()
        current_version = row[0] if row and row[0] is not None else 0
        
        applied_count = 0
        for version, desc, sql in MIGRATIONS:
            if version > current_version:
                logger.info(f"Applying migration v{version}: {desc}")
                if sql:
                    cursor.executescript(sql)
                cursor.execute(
                    "INSERT INTO _schema_version (version, description) VALUES (?, ?);",
                    (version, desc)
                )
                conn.commit()
                applied_count += 1
                
        logger.info(f"Database migrations complete. Schema version: {max(current_version, CURRENT_SCHEMA_VERSION)}.")
        return applied_count
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migrations()
