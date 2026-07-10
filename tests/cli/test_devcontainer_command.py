"""CLI integration tests for the devcontainer command."""

import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("litellm.completion")
def test_cli_devcontainer_success(mock_completion, tmp_path, temp_zero_dir) -> None:
    """Test that zero devcontainer auto-detects tech stack and generates devcontainer configurations."""
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
    
    # Create some dummy files to trigger tech stack detection
    (workspace / "app.py").write_text("print('hello')", encoding="utf-8")
    (workspace / "requirements.txt").write_text("flask", encoding="utf-8")

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM response containing File: devcontainer.json and File: Dockerfile
        llm_response = (
            "File: devcontainer.json\n"
            "```json\n"
            "{\n"
            "  \"name\": \"Python Dev Container\"\n"
            "}\n"
            "```\n\n"
            "File: Dockerfile\n"
            "```dockerfile\n"
            "FROM mcr.microsoft.com/devcontainers/python:3\n"
            "```"
        )
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=llm_response))]
        )
        
        result = runner.invoke(app, ["devcontainer"])
        
        assert result.exit_code == 0
        assert "Dev Container configuration files created" in result.stdout
        
        # Verify files were created
        devcontainer_json = workspace / ".devcontainer" / "devcontainer.json"
        dockerfile = workspace / ".devcontainer" / "Dockerfile"
        
        assert devcontainer_json.exists()
        assert dockerfile.exists()
        
        assert "Python Dev Container" in devcontainer_json.read_text(encoding="utf-8")
        assert "python:3" in dockerfile.read_text(encoding="utf-8")
    finally:
        os.chdir(old_cwd)
