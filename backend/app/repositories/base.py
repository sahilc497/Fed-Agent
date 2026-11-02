import sqlite3
from typing import Generic, Type, TypeVar, Optional, List, Any
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Any):
        self.model = model
        self.db = db

    def _get_conn(self) -> sqlite3.Connection:
        if hasattr(self.db, "conn"):
            return self.db.conn
        return self.db

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        conn = self._get_conn()
        table = getattr(self.model, "__tablename__", self.model.__name__.lower())
        cursor = conn.execute(f"SELECT * FROM {table} WHERE id = ? LIMIT 1;", (id,))
        row = cursor.fetchone()
        return self.model.from_row(row) if row else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        conn = self._get_conn()
        table = getattr(self.model, "__tablename__", self.model.__name__.lower())
        cursor = conn.execute(f"SELECT * FROM {table} LIMIT ? OFFSET ?;", (limit, skip))
        rows = cursor.fetchall()
        return [self.model.from_row(r) for r in rows]

    async def create(self, obj: ModelType) -> ModelType:
        conn = self._get_conn()
        table = getattr(self.model, "__tablename__", self.model.__name__.lower())
        import datetime
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(obj, "created_at") and getattr(obj, "created_at") is None:
            obj.created_at = now_str
        if hasattr(obj, "updated_at") and getattr(obj, "updated_at") is None:
            obj.updated_at = now_str

        d = obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)
        # Pop None id if integer primary key to let SQLite autoincrement
        if "id" in d and d["id"] is None:
            d.pop("id")
        
        # Fetch valid columns from SQLite table info
        col_info = conn.execute(f"PRAGMA table_info({table});").fetchall()
        valid_cols = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in col_info}

        # Serialize dict/list values to JSON strings if needed
        import json
        clean_d = {}
        for k, v in d.items():
            if k not in valid_cols:
                continue
            if isinstance(v, (dict, list)):
                clean_d[k] = json.dumps(v)
            elif isinstance(v, bool):
                clean_d[k] = 1 if v else 0
            else:
                clean_d[k] = v

        columns = list(clean_d.keys())
        placeholders = ["?"] * len(columns)
        values = list(clean_d.values())
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
        cursor = conn.execute(query, values)
        if hasattr(obj, "id") and getattr(obj, "id") is None and cursor.lastrowid:
            obj.id = cursor.lastrowid
        return obj

    async def delete(self, id: Any) -> bool:
        conn = self._get_conn()
        table = getattr(self.model, "__tablename__", self.model.__name__.lower())
        conn.execute(f"DELETE FROM {table} WHERE id = ?;", (id,))
        return True
