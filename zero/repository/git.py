from pathlib import Path
from typing import Dict, Any
from zero.services.logging import logger

def get_git_metrics(repo_path: Path) -> Dict[str, Any]:
    """
    Retrieve Git repository metrics using gitpython.
    If the directory is not a Git repo or Git is not installed,
    returns empty metrics/fallbacks gracefully without raising errors.
    """
    metrics: Dict[str, Any] = {
        "git_branch": None,
        "git_commit_hash": None,
        "git_commit_message": None,
        "git_is_dirty": False,
        "git_uncommitted_changes": [],
        "git_untracked_files": []
    }
    
    try:
        import git
    except ImportError:
        logger.debug("gitpython package is not installed.")
        return metrics

    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        logger.debug(f"Path {repo_path} is not a Git repository.")
        return metrics
    except Exception as e:
        logger.debug(f"Failed to check git repository: {e}")
        return metrics

    try:
        if repo.head.is_detached:
            metrics["git_branch"] = "DETACHED_HEAD"
        else:
            try:
                metrics["git_branch"] = repo.active_branch.name
            except Exception:
                metrics["git_branch"] = "DETACHED_HEAD"
                
        try:
            head_commit = repo.head.commit
            metrics["git_commit_hash"] = head_commit.hexsha
            if head_commit.message:
                metrics["git_commit_message"] = head_commit.message.splitlines()[0].strip()
        except Exception as e:
            logger.debug(f"Failed to get git commit details: {e}")

        metrics["git_is_dirty"] = repo.is_dirty(untracked_files=True)

        uncommitted = set()
        try:
            for diff in repo.index.diff(None):
                if diff.a_path:
                    uncommitted.add(diff.a_path)
            if repo.head.is_valid():
                for diff in repo.index.diff("HEAD"):
                    if diff.a_path:
                        uncommitted.add(diff.a_path)
        except Exception as e:
            logger.debug(f"Failed to check git diff: {e}")
            
        metrics["git_uncommitted_changes"] = sorted(list(uncommitted))

        try:
            metrics["git_untracked_files"] = sorted(repo.untracked_files)
        except Exception as e:
            logger.debug(f"Failed to get untracked files: {e}")

    except Exception as e:
        logger.warning(f"Error extracting Git metrics: {e}")

    return metrics
