import datetime
import json
from typing import Any, Dict, Optional


class SqliteRecord:
    """
    Lightweight base record for SQLite rows supporting dot-notation attribute access,
    dict-like subscripting, and automatic property handling.
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __contains__(self, item):
        return hasattr(self, item)

    def get(self, item, default=None):
        return getattr(self, item, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

    @classmethod
    def from_row(cls, row: Any):
        if row is None:
            return None
        if isinstance(row, dict):
            return cls(**row)
        try:
            return cls(**dict(row))
        except Exception:
            return cls(**row.__dict__)


# Alias for backward compatibility
Base = SqliteRecord
