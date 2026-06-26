import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from zero.services.logging import logger

class SQLiteDatabase:
    """Manages SQLite database connections and execution of schema migrations."""
    
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialize_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get a configured sqlite3 connection. Enable foreign keys."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _initialize_db(self) -> None:
        """Create standard tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        queries = [
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                token_count INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_path TEXT PRIMARY KEY,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT NOT NULL,
                problem TEXT NOT NULL,
                solution TEXT NOT NULL,
                status TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS global_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        ]
        
        with self.get_connection() as conn:
            for q in queries:
                conn.execute(q)
            conn.commit()
        logger.debug(f"SQLite database initialized at {self.db_path}")

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        """Execute a write/update statement (insert, update, delete)."""
        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetch_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Execute a select query and return all matches as dictionary rows."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """Execute a select query and return the first matching row as a dictionary."""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
