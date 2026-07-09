"""CLI integration tests for the schema subcommand."""

import os
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


def test_cli_schema(tmp_path, temp_zero_dir) -> None:
    """Test that zero schema scans the codebase and displays models and endpoints."""
    # Create a mock file with a DB Model and a router path
    mock_dir = tmp_path / "mock_project"
    mock_dir.mkdir()
    
    mock_code = (
        "from pydantic import BaseModel\n\n"
        "class User(BaseModel):\n"
        "    id: int\n"
        "    name: str\n\n"
        "@app.get('/users')\n"
        "def get_users():\n"
        "    pass\n"
    )
    (mock_dir / "app.py").write_text(mock_code, encoding="utf-8")
    
    old_cwd = os.getcwd()
    os.chdir(mock_dir)
    try:
        result = runner.invoke(app, ["schema"])
        assert result.exit_code == 0
        assert "Workspace Structural Schema Map" in result.stdout
        assert "Database Models & Schemas" in result.stdout
        assert "REST API Router Endpoints" in result.stdout
        assert "User" in result.stdout
        assert "get_users" in result.stdout
    finally:
        os.chdir(old_cwd)
