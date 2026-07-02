from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

class MockDelta:
    def __init__(self, content: str) -> None:
        self.content = content

class MockChoice:
    def __init__(self, content: str) -> None:
        self.delta = MockDelta(content)

class MockChunk:
    def __init__(self, content: str) -> None:
        self.choices = [MockChoice(content)]

async def mock_pr_stream(*args, **kwargs):
    yield MockChunk("BRANCH: feat/test-branch\nCOMMIT: feat(test): test changes\nTITLE: Test Title\nBODY:\nPR Body here")

def _setup_provider(temp_zero_dir: Path) -> None:
    (temp_zero_dir / "providers.toml").write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")

@patch("litellm.acompletion")
@patch("git.Repo")
@patch("shutil.which")
def test_pr_command_dirty_repo(mock_which, mock_git_repo, mock_acompletion, temp_zero_dir) -> None:
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_pr_stream
    mock_which.return_value = None  # Mock no gh client installed
    
    # Mock Git Repo
    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True
    mock_repo.untracked_files = []
    mock_repo.git.diff.return_value = "Mock Diff output"
    mock_repo.active_branch.name = "main"
    mock_repo.head.is_detached = False
    
    # Mock remote
    mock_remote = MagicMock()
    mock_remote.url = "https://github.com/owner/repo.git"
    mock_repo.remotes.origin = mock_remote
    
    mock_git_repo.return_value = mock_repo
    
    result = runner.invoke(app, [
        "pr",
        "--yes"
    ])
    
    assert result.exit_code == 0
    assert "Zero Action Git Auto-Pilot" in result.stdout
    assert "Proposed Git Actions" in result.stdout
    assert "feat/test-branch" in result.stdout
    assert "feat(test): test changes" in result.stdout
    # Stage, checkout, commit checks
    mock_repo.git.add.assert_called_with(A=True)
    mock_repo.git.checkout.assert_called_with("-b", "feat/test-branch")
    mock_repo.git.commit.assert_called_with("-m", "feat(test): test changes")
    mock_repo.git.push.assert_called_with("-u", "origin", "feat/test-branch")
