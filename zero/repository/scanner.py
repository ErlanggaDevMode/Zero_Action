from pathlib import Path
from typing import List, Dict, Any, Generator
import pathspec
from zero.services.logging import logger

def get_gitignore_spec(repo_path: Path) -> pathspec.PathSpec:
    """Load and compile root .gitignore if it exists, otherwise return an empty spec."""
    gitignore_path = repo_path / ".gitignore"
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            return pathspec.PathSpec.from_lines("gitignore", lines)
        except Exception as e:
            logger.warning(f"Failed to read .gitignore at {gitignore_path}: {e}")
    return pathspec.PathSpec.from_lines("gitignore", [])

def scan_repository(repo_path: Path) -> List[Dict[str, Any]]:
    """
    Walk the directory recursively.
    Respects .gitignore rules.
    Always ignores standard build / cache directories.
    Returns metadata for each scanned file:
    [
        {"relative_path": "path/to/file.py", "extension": ".py", "size_bytes": 1024}
    ]
    """
    spec = get_gitignore_spec(repo_path)
    
    # Standard ignore patterns for directories/files to skip scanning entirely
    standard_ignores = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".egg-info", ".pytest_cache", ".mypy_cache"}
    
    scanned_files = []
    
    def walk_dir(current_dir: Path) -> Generator[Path, None, None]:
        for p in current_dir.iterdir():
            # Check standard ignores
            if p.name in standard_ignores:
                continue
            
            # Check gitignore match using path relative to repo_path
            rel_path_str = str(p.relative_to(repo_path)).replace("\\", "/")
            
            if p.is_dir():
                if spec.match_file(rel_path_str + "/"):
                    continue
                yield from walk_dir(p)
            else:
                if spec.match_file(rel_path_str):
                    continue
                yield p

    try:
        for file_path in walk_dir(repo_path):
            try:
                rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                size = file_path.stat().st_size
                scanned_files.append({
                    "relative_path": rel_path,
                    "extension": file_path.suffix.lower(),
                    "size_bytes": size
                })
            except Exception as e:
                logger.debug(f"Failed to read file stats for {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error walking repository path {repo_path}: {e}")
        
    return scanned_files
