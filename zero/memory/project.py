from typing import Optional
from zero.storage.sqlite import SQLiteDatabase

class ProjectMemory:
    """Manages project and repository metadata storage in SQLite database."""
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save_project_summary(self, project_path: str, summary_json: str) -> None:
        """Save or overwrite a project summary."""
        self.db.execute(
            "INSERT OR REPLACE INTO projects (project_path, last_scanned, summary) VALUES (?, CURRENT_TIMESTAMP, ?);",
            (project_path, summary_json)
        )

    def get_project_summary(self, project_path: str) -> Optional[str]:
        """Retrieve a project summary if it exists."""
        row = self.db.fetch_one("SELECT summary FROM projects WHERE project_path = ?;", (project_path,))
        return row["summary"] if row else None
