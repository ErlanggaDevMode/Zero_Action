"""CLI integration tests for the memory git command."""

import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


class MockAuthor:
    def __init__(self, name):
        self.name = name


class MockCommit:
    def __init__(self, author_name, message, hexsha):
        self.author = MockAuthor(author_name)
        self.message = message
        self.hexsha = hexsha
        self.parents = []


@patch("git.Repo")
@patch("litellm.completion")
def test_cli_memory_git_success(mock_completion, mock_repo_class, tmp_path, temp_zero_dir) -> None:
    """Test that zero memory git runs successfully, analyzes git history, and stores insights."""
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

    # Configure mock git repo
    mock_repo = MagicMock()
    mock_commit = MockCommit("Test Author", "feat: initial commit", "abcdef1234567890")
    mock_repo.iter_commits.return_value = [mock_commit]
    mock_repo_class.return_value = mock_repo

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM chat response
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="AI-generated summary of commit conventions."))]
        )
        
        result = runner.invoke(app, ["memory", "git"])
        
        assert result.exit_code == 0
        assert "Developer" in result.stdout
        assert "Contribution" in result.stdout
        assert "AI Git Insights" in result.stdout
        assert "Test Author" in result.stdout
        assert "AI-generated summary of" in result.stdout
    finally:
        os.chdir(old_cwd)
