import os
import json
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

def test_init_command_success(tmp_path, temp_zero_dir) -> None:
    # 1. Create a dummy repository directory
    workspace = tmp_path / "mock_repo"
    workspace.mkdir()
    
    # Create files
    (workspace / "main.py").write_text("print('hello')")
    (workspace / "requirements.txt").write_text("fastapi>=0.1.0\n")
    (workspace / "Dockerfile").write_text("FROM python:3.12")
    
    # Gitignore
    (workspace / ".gitignore").write_text("ignored_file.txt\n")
    (workspace / "ignored_file.txt").write_text("secrets")
    
    # 2. Change current working directory to the mock workspace
    old_cwd = os.getcwd()
    os.chdir(workspace)
    
    try:
        # Run zero init command
        result = runner.invoke(app, ["init"])
        
        # Verify output details
        assert result.exit_code == 0
        assert "Repository summary cached" in result.stdout
        assert "Total Files" in result.stdout
        assert "Total Size" in result.stdout
        assert "Python" in result.stdout
        assert "Languages" in result.stdout
        assert "FastAPI" in result.stdout
        
        # Check cache
        cache_file = temp_zero_dir / "cache" / "repo_summary.json"
        assert cache_file.exists()
        
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert data["total_files"] == 4
        assert data["languages"]["Python"] == 1
        assert data["languages"]["Docker"] == 1
        assert "fastapi" in data["dependencies"]
        assert "FastAPI" in data["frameworks"]
        assert data["has_docker"] is True
        
    finally:
        os.chdir(old_cwd)
