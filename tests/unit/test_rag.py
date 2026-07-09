import pytest
from zero.storage.sqlite import SQLiteDatabase
from zero.storage.vector import SQLiteVectorStore, serialize_vector, deserialize_vector
from zero.memory.embeddings import chunk_text

def test_vector_serialization():
    vector = [0.1, -0.2, 0.35, 1.0]
    serialized = serialize_vector(vector)
    assert isinstance(serialized, bytes)
    assert len(serialized) == 16  # 4 floats * 4 bytes each
    
    deserialized = deserialize_vector(serialized)
    assert len(deserialized) == 4
    assert deserialized == pytest.approx(vector)

def test_chunk_text():
    text = "line1\nline2\nline3\nline4\nline5\nline6"
    chunks = chunk_text(text, chunk_size=10, overlap=5)
    assert len(chunks) > 1
    # Check that chunks contain some content from lines
    assert "line1" in chunks[0]
    
    empty_chunks = chunk_text("")
    assert empty_chunks == []

def test_sqlite_vector_store(tmp_path):
    db_path = tmp_path / "test_memory.db"
    db = SQLiteDatabase(db_path)
    store = SQLiteVectorStore(db)
    
    # Check table existence
    rows = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table' AND name='file_chunks';")
    assert len(rows) == 1
    
    # Save a chunk
    file_path = "src/main.py"
    store.save_chunk(file_path, 0, "def main(): print('hello')", [1.0, 0.0, 0.0])
    store.save_chunk(file_path, 1, "if __name__ == '__main__': main()", [0.0, 1.0, 0.0])
    
    # Verify save
    chunks = db.fetch_all("SELECT * FROM file_chunks WHERE file_path = ? ORDER BY chunk_index;", (file_path,))
    assert len(chunks) == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["content"] == "def main(): print('hello')"
    
    # Search similar (exact match vector [1.0, 0.0, 0.0])
    results = store.search_similar([1.0, 0.0, 0.0], limit=1)
    assert len(results) == 1
    assert results[0]["file_path"] == file_path
    assert results[0]["chunk_index"] == 0
    assert results[0]["similarity"] == pytest.approx(1.0)
    
    # Delete file chunks
    store.delete_file_chunks(file_path)
    chunks_after = db.fetch_all("SELECT * FROM file_chunks WHERE file_path = ?;", (file_path,))
    assert len(chunks_after) == 0
