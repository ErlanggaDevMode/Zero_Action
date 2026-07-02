from pathlib import Path
from typing import List, Any, Optional, Callable
from zero.services.logging import logger
from zero.storage.sqlite import SQLiteDatabase
from zero.storage.vector import SQLiteVectorStore
from zero.repository.scanner import scan_repository

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks, respecting line boundaries."""
    if not text.strip():
        return []
        
    lines = text.splitlines()
    chunks = []
    current_chunk = []
    current_len = 0
    
    for line in lines:
        current_chunk.append(line)
        current_len += len(line) + 1
        if current_len >= chunk_size:
            chunks.append("\n".join(current_chunk))
            # Backtrack to capture overlap
            overlap_lines: List[str] = []
            overlap_len = 0
            for line_item in reversed(current_chunk):
                if overlap_len + len(line_item) + 1 > overlap:
                    break
                overlap_lines.insert(0, line_item)
                overlap_len += len(line_item) + 1
            current_chunk = overlap_lines
            current_len = overlap_len
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks

class RepositoryIndexer:
    """Orchestrates chunking files and generating vector embeddings using LiteLLM."""

    def __init__(self, settings: Any, config_dir: Path, repo_path: Path, db: SQLiteDatabase) -> None:
        self.settings = settings
        self.config_dir = config_dir
        self.repo_path = repo_path
        self.db = db
        self.vector_store = SQLiteVectorStore(db)

    def _get_embedding_model_and_prefix(self) -> tuple[str, str]:
        """Determine the embedding model and LiteLLM prefix to use based on the active provider."""
        provider_name = self.settings.provider.active_provider or ""
        provider_name = provider_name.lower()
        
        if provider_name == "openai":
            return "text-embedding-3-small", "openai/"
        elif provider_name == "gemini":
            return "text-embedding-004", "gemini/"
        elif provider_name == "ollama":
            # If the user has a custom model or nomic-embed-text in ollama
            # Fallback to chat model or nomic-embed-text
            ollama_conf = getattr(self.settings.provider, "ollama", None)
            model_name = ollama_conf.model if ollama_conf else "nomic-embed-text"
            return model_name, "ollama/"
        elif provider_name == "openrouter":
            return "openai/text-embedding-3-small", "openrouter/"
        elif provider_name == "azure":
            azure_conf = getattr(self.settings.provider, "azure", None)
            model_name = azure_conf.model if (azure_conf and azure_conf.model) else "text-embedding-3-small"
            return model_name, "azure/"
        else:
            # Fallback to standard OpenAI model or OpenRouter if others are selected
            return "text-embedding-3-small", ""

    def index_repository(self, progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """Scan and generate embeddings for all files in the repository."""
        from zero.services.ai import AIService
        
        # 1. Resolve Provider
        try:
            ai_service = AIService(self.settings, self.config_dir)
            provider = ai_service.get_provider()
        except Exception as e:
            logger.error(f"Cannot get active AI provider for embedding indexing: {e}")
            if progress_callback:
                progress_callback("Failed: Active provider not configured or invalid.")
            return

        model_name, prefix = self._get_embedding_model_and_prefix()
        full_model_path = prefix + model_name if prefix else model_name
        logger.info(f"Indexing repository using embedding model: {full_model_path}")

        # 2. Scan repository files
        scanned_files = scan_repository(self.repo_path)
        
        text_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".md", ".json", 
            ".toml", ".yaml", ".yml", ".txt", ".sh", ".sql", ".go", ".rs", ".c", ".h", 
            ".cpp", ".hpp", ".java", ".kt"
        }

        # Clear vector store database chunks for this repo to clean up deleted/moved files
        self.vector_store.clear_all()

        scanned_count = 0

        for file_meta in scanned_files:
            rel_path = file_meta["relative_path"]
            ext = file_meta["extension"]
            size = file_meta["size_bytes"]

            # Filter out non-text/large files
            if ext not in text_extensions or size > 300 * 1024:
                continue

            full_file_path = self.repo_path / rel_path
            if not full_file_path.exists() or not full_file_path.is_file():
                continue

            try:
                content = full_file_path.read_text(encoding="utf-8", errors="ignore")
                chunks = chunk_text(content)
                
                if not chunks:
                    continue

                if progress_callback:
                    progress_callback(f"Indexing {rel_path} ({len(chunks)} chunks)...")

                for idx, chunk in enumerate(chunks):
                    # Generate embedding
                    try:
                        emb = provider.embeddings(chunk, model=full_model_path)
                        self.vector_store.save_chunk(rel_path, idx, chunk, emb)
                    except Exception as emb_err:
                        logger.warning(f"Failed to generate embedding for chunk {idx} of {rel_path}: {emb_err}")
                        # If a provider doesn't support embedding, skip it
                        continue
                
                scanned_count += 1
            except Exception as file_err:
                logger.error(f"Error indexing file {rel_path}: {file_err}")

        if progress_callback:
            progress_callback(f"Successfully indexed {scanned_count} files into vector database.")
