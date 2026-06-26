from pathlib import Path
import importlib
from zero.storage.sqlite import SQLiteDatabase
from zero.memory.session import SessionMemory
from zero.memory.project import ProjectMemory
from zero.memory.decision import DecisionMemory
from zero.memory.knowledge import KnowledgeMemory

# Load global.py dynamically to avoid global keyword import conflicts in standard statements
global_module = importlib.import_module("zero.memory.global")
GlobalMemory = global_module.GlobalMemory

class MemoryManager:
    """Central container that aggregates all sub-memory classes."""
    def __init__(self, db_path: Path) -> None:
        self.db = SQLiteDatabase(db_path)
        self.sessions = SessionMemory(self.db)
        self.projects = ProjectMemory(self.db)
        self.decisions = DecisionMemory(self.db)
        self.global_store = GlobalMemory(self.db)
        self.knowledge = KnowledgeMemory(self.db)
