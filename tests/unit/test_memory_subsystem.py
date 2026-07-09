from zero.memory.manager import MemoryManager

def test_session_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    manager = MemoryManager(db_file)
    
    # Create session
    manager.sessions.create_session("sess-1", "Test Conversation")
    
    # List sessions
    sessions = manager.sessions.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["title"] == "Test Conversation"
    
    # Add messages
    manager.sessions.add_message("msg-1", "sess-1", "user", "Hello assistant", 5)
    manager.sessions.add_message("msg-2", "sess-1", "assistant", "Hi there!", 4)
    
    # Retrieve messages
    messages = manager.sessions.get_messages("sess-1")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[0]["token_count"] == 5
    
    # Delete session
    manager.sessions.delete_session("sess-1")
    assert len(manager.sessions.list_sessions()) == 0
    # Messages should be deleted due to cascade delete
    assert len(manager.sessions.get_messages("sess-1")) == 0

def test_project_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    manager = MemoryManager(db_file)
    
    # Save project summary
    manager.projects.save_project_summary("/workspace/repo", '{"files": 10}')
    
    # Get project summary
    summary = manager.projects.get_project_summary("/workspace/repo")
    assert summary == '{"files": 10}'
    
    # Non-existent project path
    assert manager.projects.get_project_summary("/non/existent") is None

def test_decision_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    manager = MemoryManager(db_file)
    
    # Add decision
    manager.decisions.add_decision(
        decision_id="dec-1",
        project_path="/workspace/repo",
        title="Use SQLite",
        problem="Need lightweight DB",
        solution="Use SQLite instead of PostgreSQL",
        status="proposed"
    )
    
    # List decisions
    decisions = manager.decisions.list_decisions()
    assert len(decisions) == 1
    assert decisions[0]["title"] == "Use SQLite"
    assert decisions[0]["status"] == "proposed"
    
    # Filter by project path
    decisions_filtered = manager.decisions.list_decisions(project_path="/workspace/repo")
    assert len(decisions_filtered) == 1
    
    decisions_empty = manager.decisions.list_decisions(project_path="/other/repo")
    assert len(decisions_empty) == 0
    
    # Update status
    manager.decisions.update_decision_status("dec-1", "accepted")
    decisions_updated = manager.decisions.list_decisions()
    assert decisions_updated[0]["status"] == "accepted"

def test_global_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    manager = MemoryManager(db_file)
    
    # Set and get global preference
    manager.global_store.set_preference("theme", "dark")
    assert manager.global_store.get_preference("theme") == "dark"
    assert manager.global_store.get_preference("non-existent") is None

def test_knowledge_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    manager = MemoryManager(db_file)
    
    # Add knowledge documents
    manager.knowledge.add_knowledge("doc-1", "CLI Guide", "CLI supports many subcommands.", "docs/cli.md")
    manager.knowledge.add_knowledge("doc-2", "Architecture Overview", "Clean architecture principles are applied.", "docs/structure.md")
    
    # List entries
    entries = manager.knowledge.list_knowledge()
    assert len(entries) == 2
    
    # Search entries
    results = manager.knowledge.search_knowledge("architecture")
    assert len(results) == 1
    assert results[0]["title"] == "Architecture Overview"
    
    # Search content
    results_content = manager.knowledge.search_knowledge("subcommands")
    assert len(results_content) == 1
    assert results_content[0]["title"] == "CLI Guide"
