from pathlib import Path
from typing import List, Dict, Any, Tuple

def detect_docker(scanned_files: List[Dict[str, Any]]) -> Tuple[bool, bool]:
    """
    Detects whether Dockerfile and docker-compose.yml (or variants) exist.
    Returns (has_docker, has_docker_compose).
    """
    has_docker = False
    has_docker_compose = False
    
    compose_names = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}
    
    for file_info in scanned_files:
        name = Path(file_info["relative_path"]).name
        if name == "Dockerfile" or name.endswith(".dockerfile"):
            has_docker = True
        elif name.lower() in compose_names:
            has_docker_compose = True
            
    return has_docker, has_docker_compose
