import json
import re
from pathlib import Path
from typing import List, Set
from zero.services.logging import logger

try:
    import tomllib  # Python 3.11+ standard library
except ImportError:
    import tomllib as tomllib  # type: ignore

def parse_requirements_txt(content: str) -> List[str]:
    """Parse requirements.txt contents to extract clean package names."""
    deps = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        match = re.match(r"^([a-zA-Z0-9_\-]+)", line)
        if match:
            deps.append(match.group(1).lower())
    return deps

def parse_pyproject_toml(content: str) -> List[str]:
    """Parse pyproject.toml to extract project dependencies."""
    deps = []
    try:
        data = tomllib.loads(content)
        project = data.get("project", {})
        if isinstance(project, dict):
            for dep_str in project.get("dependencies", []):
                match = re.match(r"^([a-zA-Z0-9_\-]+)", dep_str.strip())
                if match:
                    deps.append(match.group(1).lower())
                    
        tool = data.get("tool", {})
        if isinstance(tool, dict):
            poetry = tool.get("poetry", {})
            if isinstance(poetry, dict):
                poetry_deps = poetry.get("dependencies", {})
                if isinstance(poetry_deps, dict):
                    for name in poetry_deps.keys():
                        if name.lower() != "python":
                            deps.append(name.lower())
    except Exception as e:
        logger.debug(f"Failed to parse pyproject.toml: {e}")
    return deps

def parse_package_json(content: str) -> List[str]:
    """Parse package.json dependencies and devDependencies."""
    deps = []
    try:
        data = json.loads(content)
        for key in ["dependencies", "devDependencies"]:
            val = data.get(key, {})
            if isinstance(val, dict):
                for dep_name in val.keys():
                    deps.append(dep_name.lower())
    except Exception as e:
        logger.debug(f"Failed to parse package.json: {e}")
    return deps

def parse_go_mod(content: str) -> List[str]:
    """Parse go.mod dependencies."""
    deps = []
    in_require_block = False
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("require ("):
            in_require_block = True
            continue
        if in_require_block and line == ")":
            in_require_block = False
            continue
        
        if in_require_block:
            parts = line.split()
            if parts:
                deps.append(parts[0])
        elif line.startswith("require "):
            parts = line.split()
            if len(parts) >= 2:
                deps.append(parts[1])
    return deps

def parse_cargo_toml(content: str) -> List[str]:
    """Parse Cargo.toml dependencies."""
    deps = []
    try:
        data = tomllib.loads(content)
        for key in ["dependencies", "dev-dependencies", "build-dependencies"]:
            section = data.get(key, {})
            if isinstance(section, dict):
                for dep_name in section.keys():
                    deps.append(dep_name.lower())
    except Exception as e:
        logger.debug(f"Failed to parse Cargo.toml: {e}")
    return deps

def extract_dependencies(scanned_files: List[dict], repo_path: Path) -> List[str]:
    """Search for manifest files and extract all unique dependencies."""
    all_deps: Set[str] = set()
    
    for file_info in scanned_files:
        rel_path = file_info["relative_path"]
        file_name = Path(rel_path).name
        full_path = repo_path / rel_path
        
        if not full_path.exists():
            continue
            
        try:
            if file_name == "requirements.txt" or file_name.endswith("-requirements.txt"):
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                all_deps.update(parse_requirements_txt(content))
            elif file_name == "pyproject.toml":
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                all_deps.update(parse_pyproject_toml(content))
            elif file_name == "package.json":
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                all_deps.update(parse_package_json(content))
            elif file_name == "go.mod":
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                all_deps.update(parse_go_mod(content))
            elif file_name == "Cargo.toml":
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                all_deps.update(parse_cargo_toml(content))
        except Exception as e:
            logger.warning(f"Error reading dependency file {file_name}: {e}")
            
    return sorted(list(all_deps))
