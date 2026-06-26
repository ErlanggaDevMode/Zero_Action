from typing import List, Dict, Any, Optional
from zero.storage.sqlite import SQLiteDatabase

class SessionMemory:
    """Handles chat session loading and saving from SQLite database."""
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def create_session(self, session_id: str, title: str) -> None:
        """Create a new chat session."""
        self.db.execute(
            "INSERT OR REPLACE INTO sessions (id, title, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP);",
            (session_id, title)
        )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by its ID."""
        return self.db.fetch_one("SELECT * FROM sessions WHERE id = ?;", (session_id,))

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all chat sessions, sorted by last updated time."""
        return self.db.fetch_all("SELECT * FROM sessions ORDER BY updated_at DESC;")

    def delete_session(self, session_id: str) -> None:
        """Delete a chat session and all its messages."""
        self.db.execute("DELETE FROM sessions WHERE id = ?;", (session_id,))

    def add_message(self, message_id: str, session_id: str, role: str, content: str, token_count: int = 0) -> None:
        """Add a message to a session and touch the session's updated_at field."""
        self.db.execute(
            "INSERT INTO messages (id, session_id, role, content, token_count) VALUES (?, ?, ?, ?, ?);",
            (message_id, session_id, role, content, token_count)
        )
        self.db.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (session_id,)
        )

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages for a session ordered by creation time."""
        return self.db.fetch_all("SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC;", (session_id,))
