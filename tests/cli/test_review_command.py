from unittest.mock import patch
from pathlib import Path
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Mock streaming helpers
# ---------------------------------------------------------------------------

class MockDelta:
    def __init__(self, content: str) -> None:
        self.content = content

class MockChoice:
    def __init__(self, content: str) -> None:
        self.delta = MockDelta(content)

class MockChunk:
    def __init__(self, content: str) -> None:
        self.choices = [MockChoice(content)]

async def mock_review_stream(*args, **kwargs):
    yield MockChunk("# Code Review: test.py\n\n")
    yield MockChunk("## Summary\nThis file looks generally well-structured.\n\n")
    yield MockChunk("## 1. Security Issues\nNo security issues detected.\n\n")
    yield MockChunk("## 7. Recommended Changes\n1. Add docstrings to all public methods.\n")

def _setup_provider(temp_zero_dir: Path) -> None:
    """Write a minimal providers.toml to temp_zero_dir."""
    (temp_zero_dir / "providers.toml").write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("litellm.acompletion")
def test_review_command_with_file(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Review a single file — output should appear on stdout."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_review_stream

    target = tmp_path / "test.py"
    target.write_text("def hello(): pass\n", encoding="utf-8")

    result = runner.invoke(app, ["review", "--file", str(target)])

    assert result.exit_code == 0
    assert "Zero Action Reviewer" in result.stdout
    assert "Review Complete" in result.stdout

@patch("litellm.acompletion")
def test_review_command_saves_output_file(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Review with --output should write the review to disk."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_review_stream

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")
    out_file = tmp_path / "review_report.md"

    result = runner.invoke(app, [
        "review",
        "--file", str(target),
        "--output", str(out_file),
    ])

    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "# Code Review" in content
    assert "Security Issues" in content

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_review_command_overwrite_no(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Declining overwrite should leave the original file intact."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_review_stream
    mock_confirm.return_value = False

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")
    out_file = tmp_path / "report.md"
    out_file.write_text("original report", encoding="utf-8")

    result = runner.invoke(app, [
        "review",
        "--file", str(target),
        "--output", str(out_file),
    ])

    assert result.exit_code == 0
    assert "Skipped saving review" in result.stdout
    assert out_file.read_text(encoding="utf-8") == "original report"

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_review_command_overwrite_yes(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Confirming overwrite should replace the output file."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_review_stream
    mock_confirm.return_value = True

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")
    out_file = tmp_path / "report.md"
    out_file.write_text("original report", encoding="utf-8")

    result = runner.invoke(app, [
        "review",
        "--file", str(target),
        "--output", str(out_file),
    ])

    assert result.exit_code == 0
    content = out_file.read_text(encoding="utf-8")
    assert "# Code Review" in content
    assert "original report" not in content

def test_review_command_file_not_found(temp_zero_dir) -> None:
    """Passing a non-existent file should exit with code 1 and a clear error."""
    _setup_provider(temp_zero_dir)

    result = runner.invoke(app, ["review", "--file", "nonexistent_file.py"])

    assert result.exit_code == 1
    assert "not found" in result.stdout

def test_review_command_no_provider(tmp_path) -> None:
    """Missing provider configuration should exit with code 1 and helpful message."""
    import os
    env_home = str(tmp_path)
    with patch.dict(os.environ, {"ZERO_HOME": env_home}):
        result = runner.invoke(app, ["review", "--file", str(tmp_path)])

    assert result.exit_code == 1

@patch("litellm.acompletion")
def test_review_command_focus_filter(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """--focus option should be accepted and passed through without error."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_review_stream

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")

    result = runner.invoke(app, [
        "review",
        "--file", str(target),
        "--focus", "security,performance",
    ])

    assert result.exit_code == 0
    assert "security" in result.stdout

@patch("litellm.acompletion")
def test_review_command_invalid_focus(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Invalid --focus area should exit with code 1 and list valid options."""
    _setup_provider(temp_zero_dir)

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")

    result = runner.invoke(app, [
        "review",
        "--file", str(target),
        "--focus", "speed,typos",
    ])

    assert result.exit_code == 1
    assert "Unknown focus area" in result.stdout

@patch("litellm.acompletion")
def test_review_command_dir(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Reviewing a directory should collect all source files and review each."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_review_stream

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.py").write_text("a = 1\n", encoding="utf-8")
    (src_dir / "b.py").write_text("b = 2\n", encoding="utf-8")

    result = runner.invoke(app, ["review", "--dir", str(src_dir)])

    assert result.exit_code == 0
    assert "2" in result.stdout  # "Found 2 file(s)"
    assert "Review Complete" in result.stdout

def test_review_command_file_and_dir_exclusive(temp_zero_dir, tmp_path) -> None:
    """Passing both --file and --dir should exit with code 1."""
    _setup_provider(temp_zero_dir)

    f = tmp_path / "x.py"
    f.write_text("x = 1\n", encoding="utf-8")

    result = runner.invoke(app, [
        "review",
        "--file", str(f),
        "--dir", str(tmp_path),
    ])

    assert result.exit_code == 1
    assert "not both" in result.stdout
