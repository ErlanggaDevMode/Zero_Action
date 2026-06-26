from pathlib import Path
from zero.repository.scanner import scan_repository
from zero.repository.language import detect_languages
from zero.repository.dependency import extract_dependencies
from zero.repository.framework import detect_frameworks
from zero.repository.docker import detect_docker
from zero.repository.git import get_git_metrics
from zero.repository.summary import RepositorySummary

def analyze_repository(repo_path: Path) -> RepositorySummary:
    """
    Scans and analyzes the repository to produce a unified RepositorySummary.
    """
    scanned_files = scan_repository(repo_path)
    
    total_files = len(scanned_files)
    total_size = sum(f["size_bytes"] for f in scanned_files)
    
    languages = detect_languages(scanned_files, repo_path)
    dependencies = extract_dependencies(scanned_files, repo_path)
    frameworks = detect_frameworks(scanned_files, dependencies, repo_path)
    has_docker, has_docker_compose = detect_docker(scanned_files)
    git_metrics = get_git_metrics(repo_path)
    
    return RepositorySummary(
        total_files=total_files,
        total_size_bytes=total_size,
        languages=languages,
        dependencies=dependencies,
        frameworks=frameworks,
        has_docker=has_docker,
        has_docker_compose=has_docker_compose,
        **git_metrics
    )
