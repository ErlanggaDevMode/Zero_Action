"""CLI integration tests for the release command."""

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


@patch("git.Repo")
@patch("litellm.completion")
def test_cli_release_success(mock_completion, mock_repo_class, tmp_path, temp_zero_dir) -> None:
    """Test that zero release generates release notes and updates CHANGELOG.md."""
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
    mock_commit = MockCommit("Tester", "feat: implement benchmark command", "1234567890abcdef")
    mock_repo.iter_commits.return_value = [mock_commit]
    mock_repo.tags = []
    mock_repo_class.return_value = mock_repo

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM response
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="### Features\n- Implement benchmark command"))]
        )
        
        result = runner.invoke(app, [
            "release",
            "--version", "v1.1.0"
        ])
        
        assert result.exit_code == 0
        assert "Created CHANGELOG.md" in result.stdout
        assert "Implement benchmark command" in result.stdout
        
        # Verify CHANGELOG.md was created
        changelog_file = workspace / "CHANGELOG.md"
        assert changelog_file.exists()
        content = changelog_file.read_text(encoding="utf-8")
        assert "## v1.1.0" in content
        assert "### Features" in content
    finally:
        os.chdir(old_cwd)
