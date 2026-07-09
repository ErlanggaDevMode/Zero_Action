"""CLI integration tests for the docker autopilot subcommand."""

import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("subprocess.run")
def test_cli_docker_already_has_configs(mock_run, tmp_path, temp_zero_dir) -> None:
    """Test that zero docker runs compose when configs already exist."""
    # 1. Setup active provider in settings/TOML
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""", encoding="utf-8")

    workspace = tmp_path / "mock_project"
    workspace.mkdir()
    
    (workspace / "Dockerfile").write_text("FROM python", encoding="utf-8")
    (workspace / "docker-compose.yml").write_text("version: '3'", encoding="utf-8")
    
    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock subprocess runs
        # First call: docker compose up --build -d
        # Second call: docker compose logs --tail=40
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Successfully built", stderr=""),
            MagicMock(returncode=0, stdout="No errors", stderr="")
        ]
        
        result = runner.invoke(app, ["docker"])
        assert result.exit_code == 0
        assert "Building and starting containers using docker-compose..." in result.stdout
        assert "Containers started successfully" in result.stdout
    finally:
        os.chdir(old_cwd)
