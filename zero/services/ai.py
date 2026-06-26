import json
from pathlib import Path
from typing import Any
from zero.providers.manager import ProviderManager
from zero.services.config import ZeroSettings
from zero.services.logging import logger

class AIService:
    """Orchestrates AI model completions and compiles workspace context prompts."""

    def __init__(self, settings: ZeroSettings, config_dir: Path) -> None:
        self.settings = settings
        self.config_dir = config_dir
        self.provider_manager = ProviderManager(settings)

    def get_system_prompt(self, repo_path: Path) -> str:
        """Compile system prompt with repository intelligence metrics if cached summary exists."""
        base_prompt = "You are Zero Action, an elite software engineering partner CLI."
        
        cache_path = self.config_dir / "cache" / "repo_summary.json"
        if cache_path.exists():
            try:
                summary_data = json.loads(cache_path.read_text(encoding="utf-8"))
                
                context_lines = [
                    "\n---",
                    "CURRENT WORKSPACE CONTEXT:",
                    f"Path: {repo_path.resolve()}",
                    f"Total files: {summary_data.get('total_files', 0)}",
                    f"Total size: {summary_data.get('total_size_bytes', 0)} bytes",
                ]
                
                langs = summary_data.get("languages", {})
                if langs:
                    context_lines.append(f"Languages: {', '.join(f'{k} ({v} files)' for k, v in langs.items())}")
                    
                frameworks = summary_data.get("frameworks", [])
                if frameworks:
                    context_lines.append(f"Frameworks: {', '.join(frameworks)}")
                    
                git_branch = summary_data.get("git_branch")
                if git_branch:
                    context_lines.append(f"Git branch: {git_branch}")
                    status = "dirty" if summary_data.get("git_is_dirty") else "clean"
                    context_lines.append(f"Git status: {status}")
                    
                context_lines.append("---")
                
                return base_prompt + "\n" + "\n".join(context_lines)
            except Exception as e:
                logger.warning(f"Failed to read/compile repository summary cache: {e}")
                
        return base_prompt

    def get_provider(self) -> Any:
        """Retrieve the configured active provider instance."""
        return self.provider_manager.get_provider()
