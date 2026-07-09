"""CLI integration tests for the refactor command."""

import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("litellm.completion")
@patch("subprocess.run")
def test_cli_refactor_success(mock_run, mock_completion, tmp_path, temp_zero_dir) -> None:
    """Test that zero refactor successfully modifies a file and passes checks."""
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
    
    # Initialize a mock git repo
    from git import Repo
    repo = Repo.init(workspace)
    
    target_file = workspace / "foo.py"
    target_file.write_text("def run():\n    pass\n", encoding="utf-8")
    
    # Add and commit so git status is clean
    repo.index.add(["foo.py"])
    repo.index.commit("initial commit")
    
    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM response
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="```python\ndef run():\n    print('refactored')\n```"))]
        )
        
        # Mock subprocess quality checks (ruff and pytest success)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # ruff
            MagicMock(returncode=0, stdout="", stderr="")  # pytest
        ]
        
        result = runner.invoke(app, [
            "refactor",
            "--file", "foo.py",
            "--instruction", "add print statement"
        ])
        
        assert result.exit_code == 0
        assert "Refactoring target: foo.py" in result.stdout
        assert "refactor/fix attempts" not in result.stdout
        assert target_file.read_text(encoding="utf-8").strip() == "def run():\n    print('refactored')"
    finally:
        os.chdir(old_cwd)
