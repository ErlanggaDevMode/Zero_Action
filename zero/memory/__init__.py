import importlib
from zero.memory.manager import MemoryManager
from zero.memory.session import SessionMemory
from zero.memory.project import ProjectMemory
from zero.memory.decision import DecisionMemory
from zero.memory.knowledge import KnowledgeMemory

global_module = importlib.import_module("zero.memory.global")
GlobalMemory = global_module.GlobalMemory

__all__ = [
    "MemoryManager",
    "SessionMemory",
    "ProjectMemory",
    "DecisionMemory",
    "GlobalMemory",
    "KnowledgeMemory"
]
