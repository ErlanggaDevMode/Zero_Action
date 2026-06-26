from typing import Optional
from zero.storage.sqlite import SQLiteDatabase

class GlobalMemory:
    """Manages global key-value preference storage in SQLite database."""
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def set_preference(self, key: str, value: str) -> None:
        """Store a global preference value."""
        self.db.execute(
            "INSERT OR REPLACE INTO global_store (key, value) VALUES (?, ?);",
            (key, value)
        )

    def get_preference(self, key: str) -> Optional[str]:
        """Retrieve a global preference value."""
        row = self.db.fetch_one("SELECT value FROM global_store WHERE key = ?;", (key,))
        return row["value"] if row else None
