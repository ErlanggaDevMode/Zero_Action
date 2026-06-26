from typing import List, Dict, Any, Optional
from zero.storage.sqlite import SQLiteDatabase

class KnowledgeMemory:
    """Manages raw imported knowledge files/reference logs in SQLite database."""
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def add_knowledge(self, knowledge_id: str, title: str, content: str, source: Optional[str] = None) -> None:
        """Add or overwrite a knowledge document."""
        self.db.execute(
            "INSERT OR REPLACE INTO knowledge (id, title, content, source, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);",
            (knowledge_id, title, content, source)
        )

    def list_knowledge(self) -> List[Dict[str, Any]]:
        """List all imported knowledge entries."""
        return self.db.fetch_all("SELECT * FROM knowledge ORDER BY created_at DESC;")

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base using a simple substring lookup on title and content."""
        search_pattern = f"%{query}%"
        return self.db.fetch_all(
            "SELECT * FROM knowledge WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC;",
            (search_pattern, search_pattern)
        )
