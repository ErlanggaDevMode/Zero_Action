from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class RepositorySummary(BaseModel):
    """Consolidated representation of repository metrics, technologies, and status."""
    total_files: int = Field(default=0, description="Total number of scanned files")
    total_size_bytes: int = Field(default=0, description="Total size of scanned files in bytes")
    languages: Dict[str, int] = Field(default_factory=dict, description="Files count per language")
    dependencies: List[str] = Field(default_factory=list, description="Extracted package/library dependencies")
    frameworks: List[str] = Field(default_factory=list, description="Detected web/application frameworks")
    has_docker: bool = Field(default=False, description="Whether a Dockerfile is present")
    has_docker_compose: bool = Field(default=False, description="Whether docker-compose.yml is present")
    git_branch: Optional[str] = Field(default=None, description="Active git branch name")
    git_commit_hash: Optional[str] = Field(default=None, description="Active commit hash")
    git_commit_message: Optional[str] = Field(default=None, description="Active commit message summary")
    git_is_dirty: bool = Field(default=False, description="Whether git repository has uncommitted changes")
    git_uncommitted_changes: List[str] = Field(default_factory=list, description="Files with uncommitted changes")
    git_untracked_files: List[str] = Field(default_factory=list, description="Untracked files in git repository")
