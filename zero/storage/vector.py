import struct
from typing import List, Dict, Any
from zero.storage.sqlite import SQLiteDatabase

def serialize_vector(vector: List[float]) -> bytes:
    """Serialize a list of floats to binary bytes."""
    return struct.pack(f"{len(vector)}f", *vector)

def deserialize_vector(data: bytes) -> List[float]:
    """Deserialize binary bytes back to a list of floats."""
    if not data:
        return []
    n = len(data) // 4
    return list(struct.unpack(f"{n}f", data))

class SQLiteVectorStore:
    """Manages storage and semantic search query matching of text chunks and vector embeddings."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save_chunk(self, file_path: str, chunk_index: int, content: str, embedding: List[float]) -> None:
        """Save or update a file chunk with its embedding."""
        chunk_id = f"{file_path}:{chunk_index}"
        emb_bytes = serialize_vector(embedding)
        
        # Remove old matching ID if it exists, then insert
        self.db.execute(
            """
            INSERT OR REPLACE INTO file_chunks (id, file_path, chunk_index, content, embedding, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (chunk_id, file_path, chunk_index, content, emb_bytes)
        )

    def delete_file_chunks(self, file_path: str) -> None:
        """Delete all chunks associated with a specific file path."""
        self.db.execute(
            "DELETE FROM file_chunks WHERE file_path = ?",
            (file_path,)
        )

    def clear_all(self) -> None:
        """Clear all indexed file chunks from the store."""
        self.db.execute("DELETE FROM file_chunks")

    def search_similar(self, query_embedding: List[float], limit: int = 5, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """Find the most semantically similar chunks in the store using cosine similarity."""
        query_bytes = serialize_vector(query_embedding)
        
        # We call the custom cosine_similarity function registered on the connection
        results = self.db.fetch_all(
            """
            SELECT file_path, chunk_index, content, cosine_similarity(embedding, ?) as similarity
            FROM file_chunks
            ORDER BY similarity DESC
            LIMIT ?
            """,
            (query_bytes, limit)
        )
        
        # Filter by threshold if requested
        if min_similarity > 0.0:
            results = [r for r in results if r["similarity"] >= min_similarity]
            
        return results
