import os
import sqlite3
import logging
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager
from app.core.config import settings

logger = logging.getLogger("federated_mesh.db.sqlite")


def resolve_db_path(configured_path: Optional[str] = None) -> str:
    """
    Safely resolves the database path across Windows-native, Linux, and Docker environments.
    Ensures parent directories exist.
    """
    path_str = configured_path or settings.DATABASE_PATH
    p = Path(path_str)
    
    if not p.is_absolute():
        # Check if running from root or backend directory
        if Path("backend").is_dir():
            p = Path("backend") / p if not str(p).startswith("backend") else p
        elif Path("..").resolve().name == "Fedral-Agent" or Path("app").is_dir():
            # Already inside backend/
            if str(p).startswith("backend/"):
                p = Path(str(p).replace("backend/", "", 1))
            elif str(p).startswith("backend\\"):
                p = Path(str(p).replace("backend\\", "", 1))
    
    resolved = p.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return str(resolved)


def create_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Creates a new SQLite connection using Python's standard-library sqlite3 module.
    Enforces foreign keys, WAL mode, busy timeout, and dictionary-like row factory.
    """
    target_path = resolve_db_path(db_path)
    
    conn = sqlite3.connect(
        target_path,
        timeout=15.0,
        check_same_thread=False,
        isolation_level=None  # Managed transactions
    )
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    # 1. Enable strict foreign key enforcement
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 2. Configure WAL mode for high concurrency
    try:
        cursor.execute("PRAGMA journal_mode = WAL;")
    except Exception as e:
        logger.warning(f"Failed to enable WAL mode, falling back: {e}")
        cursor.execute("PRAGMA journal_mode = DELETE;")
        
    # 3. Set busy timeout to prevent locking conflicts
    cursor.execute("PRAGMA busy_timeout = 5000;")
    # 4. Synchronous NORMAL in WAL mode provides safe durability & performance
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.close()
    
    return conn


@contextmanager
def db_transaction(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for atomic SQLite transactions using Python built-in sqlite3.
    Automatically commits on normal exit and rolls back on exception.
    """
    conn = create_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE;")
        yield conn
        if conn.in_transaction:
            conn.commit()
    except Exception as exc:
        if conn.in_transaction:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"Transaction rolled back due to error: {exc}")
        raise
    finally:
        conn.close()


class SqliteSession:
    """
    Standard-library SQLite session wrapper compatible with async/await patterns
    used by FastAPI dependency injection.
    """
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, seq_of_params) -> sqlite3.Cursor:
        return self.conn.executemany(sql, seq_of_params)

    async def commit(self):
        try:
            self.conn.commit()
        except Exception:
            pass

    async def flush(self):
        pass

    async def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        self.conn.close()

    def cursor(self) -> sqlite3.Cursor:
        return self.conn.cursor()


def get_db() -> Generator[SqliteSession, None, None]:
    """
    FastAPI dependency for request-scoped SQLite connection.
    Yields SqliteSession, safely committing any active transaction on completion
    and rolling back on exception.
    """
    conn = create_connection()
    session = SqliteSession(conn)
    try:
        yield session
        if conn.in_transaction:
            conn.commit()
    except Exception:
        if conn.in_transaction:
            try:
                conn.rollback()
            except Exception:
                pass
        raise
    finally:
        conn.close()

