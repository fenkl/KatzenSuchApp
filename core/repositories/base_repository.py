"""
Base Repository
Provides common database operations for all repositories.
"""

from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import sqlite3
from modules.db_utils import get_connection


class BaseRepository:
    """Base repository with common DB operations."""

    @contextmanager
    def get_db_connection(self):
        """Context manager for database connection."""
        conn = get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as dicts."""
        with self.get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute INSERT/UPDATE/DELETE with multiple params."""
        with self.get_db_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, params_list)
            conn.commit()

    def execute_single(self, query: str, params: tuple = (), require_lastrowid: bool = False) -> Optional[int]:
        """Execute single INSERT/UPDATE/DELETE."""
        with self.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            if require_lastrowid:
                return cur.lastrowid
            return None

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row."""
        results = self.execute_query(query, params)
        return results[0] if results else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        return self.execute_query(query, params)
