"""CLI integration tests for the pr --prune command."""

import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("git.Repo")
@patch("litellm.completion")
def test_cli_pr_prune_success(mock_completion, mock_repo_class, tmp_path, temp_zero_dir) -> None:
    """Test that zero pr --prune scans and safely deletes merged branches."""
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
    
    # Simulate list of heads: main, feat/old-feature, feat/active-feature
    mock_repo.heads = ["main", "feat/old-feature", "feat/active-feature"]
    mock_repo.active_branch.name = "feat/active-feature"
    
    # git branch --merged returns main, feat/old-feature (since they are merged to main)
    mock_repo.git.branch.return_value = "  main\n* feat/active-feature\n  feat/old-feature"
    mock_repo_class.return_value = mock_repo

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        result = runner.invoke(app, [
            "pr",
            "--prune",
            "--yes"  # Auto-approve deletion
        ])
        
        assert result.exit_code == 0
        assert "Found 1 merged local branch(es) to prune" in result.stdout
        assert "feat/old-feature" in result.stdout
        
        # Verify git delete command was called on feat/old-feature
        mock_repo.git.branch.assert_any_call("-d", "feat/old-feature")
    finally:
        os.chdir(old_cwd)
