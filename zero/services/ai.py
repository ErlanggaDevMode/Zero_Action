import json
from pathlib import Path
from typing import Any, Optional
from zero.providers.manager import ProviderManager
from zero.services.config import ZeroSettings
from zero.services.logging import logger

class AIService:
    """Orchestrates AI model completions and compiles workspace context prompts."""

    def __init__(self, settings: ZeroSettings, config_dir: Path) -> None:
        self.settings = settings
        self.config_dir = config_dir
        self.provider_manager = ProviderManager(settings)

    def get_system_prompt(self, repo_path: Path, query: Optional[str] = None) -> str:
        """Compile system prompt with repository intelligence metrics and optional semantic code chunks."""
        base_prompt = "You are Zero Action, an elite software engineering partner CLI."
        
        context_lines = []
        
        cache_path = self.config_dir / "cache" / "repo_summary.json"
        if cache_path.exists():
            try:
                summary_data = json.loads(cache_path.read_text(encoding="utf-8"))
                
                context_lines.extend([
                    "\n---",
                    "CURRENT WORKSPACE CONTEXT:",
                    f"Path: {repo_path.resolve()}",
                    f"Total files: {summary_data.get('total_files', 0)}",
                    f"Total size: {summary_data.get('total_size_bytes', 0)} bytes",
                ])
                
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
            except Exception as e:
                logger.warning(f"Failed to read/compile repository summary cache: {e}")

        # Add semantic code chunks context if a query is provided
        if query:
            try:
                from zero.storage.sqlite import SQLiteDatabase
                from zero.storage.vector import SQLiteVectorStore
                from zero.memory.embeddings import RepositoryIndexer
                
                db_path = self.config_dir / "memory.db"
                db = SQLiteDatabase(db_path)
                vector_store = SQLiteVectorStore(db)
                
                provider = self.get_provider()
                
                indexer = RepositoryIndexer(self.settings, self.config_dir, repo_path, db)
                model_name, prefix = indexer._get_embedding_model_and_prefix()
                full_model_path = prefix + model_name if prefix else model_name
                
                query_emb = provider.embeddings(query, model=full_model_path)
                similar_chunks = vector_store.search_similar(query_emb, limit=5)
                
                if similar_chunks:
                    context_lines.append("\nRELEVANT CODE CHUNKS (SEMANTIC SEARCH):")
                    context_lines.append("Use these code snippets to answer the user query accurately if relevant.")
                    for idx, chunk in enumerate(similar_chunks):
                        context_lines.extend([
                            f"\nChunk {idx+1} [File: {chunk['file_path']}, Index: {chunk['chunk_index']}]:",
                            "```",
                            chunk["content"],
                            "```"
                        ])
                    context_lines.append("---")
            except Exception as e:
                logger.warning(f"Failed to retrieve semantic code context: {e}")
                
        if context_lines:
            return base_prompt + "\n" + "\n".join(context_lines)
        return base_prompt

    def get_provider(self) -> Any:
        """Retrieve the configured active provider instance."""
        return self.provider_manager.get_provider()
