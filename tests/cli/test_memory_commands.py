from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

def test_memory_sessions_flow(temp_zero_dir) -> None:
    # 1. List sessions when empty
    result = runner.invoke(app, ["memory", "list-sessions"])
    assert result.exit_code == 0
    assert "No saved chat sessions found" in result.stdout
    
    # 2. Show session that doesn't exist
    result_show = runner.invoke(app, ["memory", "show-session", "nonexistent"])
    assert result_show.exit_code == 1
    assert "not found" in result_show.stdout
    
    # 3. Delete session that doesn't exist
    result_del = runner.invoke(app, ["memory", "delete-session", "nonexistent"])
    assert result_del.exit_code == 1
    assert "not found" in result_del.stdout

def test_memory_decisions_flow(temp_zero_dir) -> None:
    # 1. List when empty
    result_list = runner.invoke(app, ["memory", "list-decisions"])
    assert result_list.exit_code == 0
    assert "No logged technical decisions found" in result_list.stdout
    
    # 2. Add a decision interactively/via options
    result_add = runner.invoke(app, [
        "memory", "add-decision",
        "--title", "Use Pytest",
        "--problem", "Need a testing framework",
        "--solution", "Use pytest",
        "--status", "accepted"
    ])
    assert result_add.exit_code == 0
    assert "Recorded Technical Decision" in result_add.stdout
    
    # 3. List decisions and check it's present
    result_list2 = runner.invoke(app, ["memory", "list-decisions"])
    assert result_list2.exit_code == 0
    assert "Use Pytest" in result_list2.stdout
    assert "accepted" in result_list2.stdout

def test_memory_import_knowledge(tmp_path, temp_zero_dir) -> None:
    # 1. Import a file that doesn't exist
    result_err = runner.invoke(app, ["memory", "import-knowledge", "nonexistent.txt"])
    assert result_err.exit_code == 1
    assert "does not exist" in result_err.stdout
    
    # 2. Import valid file
    doc = tmp_path / "wiki.md"
    doc.write_text("# Wiki\nThis is reference wiki.")
    
    result_ok = runner.invoke(app, ["memory", "import-knowledge", str(doc)])
    assert result_ok.exit_code == 0
    assert "Knowledge base successfully imported file" in result_ok.stdout
    assert "wiki.md" in result_ok.stdout
