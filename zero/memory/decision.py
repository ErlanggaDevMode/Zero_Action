from typing import List, Dict, Any, Optional
from zero.storage.sqlite import SQLiteDatabase

class DecisionMemory:
    """Manages architectural decision records (ADRs) logs in SQLite database."""
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def add_decision(self, decision_id: str, project_path: str, title: str, problem: str, solution: str, status: str = "proposed") -> None:
        """Add or overwrite an architectural decision."""
        self.db.execute(
            "INSERT OR REPLACE INTO decisions (id, project_path, created_at, title, problem, solution, status) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?);",
            (decision_id, project_path, title, problem, solution, status)
        )

    def list_decisions(self, project_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List decisions, optionally filtered by a specific project path."""
        if project_path:
            return self.db.fetch_all(
                "SELECT * FROM decisions WHERE project_path = ? ORDER BY created_at DESC;",
                (project_path,)
            )
        return self.db.fetch_all("SELECT * FROM decisions ORDER BY created_at DESC;")

    def update_decision_status(self, decision_id: str, status: str) -> None:
        """Update the status of a specific decision."""
        self.db.execute(
            "UPDATE decisions SET status = ? WHERE id = ?;",
            (status, decision_id)
        )
