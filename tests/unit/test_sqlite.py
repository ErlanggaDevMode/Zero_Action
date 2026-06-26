import sqlite3
import pytest
from zero.storage.sqlite import SQLiteDatabase

def test_sqlite_db_init(tmp_path):
    db_file = tmp_path / "test_memory.db"
    db = SQLiteDatabase(db_file)
    
    # Confirm tables are created
    tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = {t["name"] for t in tables}
    assert "sessions" in table_names
    assert "messages" in table_names
    assert "projects" in table_names
    assert "decisions" in table_names
    assert "knowledge" in table_names
    assert "global_store" in table_names

def test_sqlite_db_operations(tmp_path):
    db_file = tmp_path / "test_memory.db"
    db = SQLiteDatabase(db_file)
    
    # Insert a session
    db.execute("INSERT INTO sessions (id, title) VALUES (?, ?);", ("session-1", "Test Session"))
    
    # Retrieve it
    row = db.fetch_one("SELECT * FROM sessions WHERE id = ?;", ("session-1",))
    assert row is not None
    assert row["title"] == "Test Session"
    
    # Insert messages
    db.execute(
        "INSERT INTO messages (id, session_id, role, content, token_count) VALUES (?, ?, ?, ?, ?);",
        ("msg-1", "session-1", "user", "Hello assistant", 10)
    )
    
    # Fetch all messages
    messages = db.fetch_all("SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC;", ("session-1",))
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello assistant"
    assert messages[0]["token_count"] == 10

def test_sqlite_db_foreign_keys(tmp_path):
    db_file = tmp_path / "test_memory.db"
    db = SQLiteDatabase(db_file)
    
    # Foreign keys constraint check: Inserting a message for an invalid session should raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?);",
            ("msg-2", "invalid-session-id", "user", "Won't insert")
        )
