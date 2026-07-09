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

FIXED_CODE = 'def hello(name: str) -> str:\n    # Fixed: added type annotation\n    return f"Hello, {name}"\n'

async def mock_fix_stream(*args, **kwargs):
    yield MockChunk(FIXED_CODE)

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
@patch("rich.prompt.Confirm.ask")
def test_fix_command_with_error_applies(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Fix with --error should stream diff and overwrite file when confirmed."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_fix_stream
    mock_confirm.return_value = True

    target = tmp_path / "hello.py"
    target.write_text('def hello(name):\n    return "Hello " + name\n', encoding="utf-8")

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
        "--error", "TypeError: missing type annotation",
    ])

    assert result.exit_code == 0
    assert "Zero Action Fixer" in result.stdout
    assert "Fix Applied" in result.stdout
    assert "type annotation" in target.read_text(encoding="utf-8")

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_fix_command_with_instruction(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Fix with --instruction should succeed and write the corrected content."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_fix_stream
    mock_confirm.return_value = True

    target = tmp_path / "src.py"
    target.write_text("def greet(): pass\n", encoding="utf-8")

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
        "--instruction", "Add a name parameter with type annotation",
    ])

    assert result.exit_code == 0
    assert "Fix Applied" in result.stdout

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_fix_command_with_review_file(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Fix using a review report file should load the report and succeed."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_fix_stream
    mock_confirm.return_value = True

    target = tmp_path / "src.py"
    target.write_text("def greet(): pass\n", encoding="utf-8")

    review_file = tmp_path / "review.md"
    review_file.write_text("## 5. Readability Issues\nFunction lacks type annotations.\n", encoding="utf-8")

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
        "--review", str(review_file),
    ])

    assert result.exit_code == 0
    assert "Loaded review report" in result.stdout
    assert "Fix Applied" in result.stdout

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_fix_command_declines_write(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """Declining the diff confirmation should leave the original file unchanged."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_fix_stream
    mock_confirm.return_value = False

    original_content = "def greet(): pass\n"
    target = tmp_path / "src.py"
    target.write_text(original_content, encoding="utf-8")

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
        "--error", "Missing type annotation",
    ])

    assert result.exit_code == 0
    assert "discarded" in result.stdout
    assert target.read_text(encoding="utf-8") == original_content

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_fix_command_to_output_file(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    """--output should write to a separate file, leaving the original untouched."""
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_fix_stream
    mock_confirm.return_value = True

    original_content = "def greet(): pass\n"
    target = tmp_path / "src.py"
    target.write_text(original_content, encoding="utf-8")
    out_file = tmp_path / "src_fixed.py"

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
        "--instruction", "Add return type",
        "--output", str(out_file),
    ])

    assert result.exit_code == 0
    assert out_file.exists()
    assert target.read_text(encoding="utf-8") == original_content  # original untouched

def test_fix_command_missing_file(temp_zero_dir) -> None:
    """Passing a non-existent file should exit with code 1 and a clear error."""
    _setup_provider(temp_zero_dir)

    result = runner.invoke(app, [
        "fix",
        "--file", "ghost_file.py",
        "--error", "SyntaxError",
    ])

    assert result.exit_code == 1
    assert "not found" in result.stdout

def test_fix_command_no_problem_specified(temp_zero_dir, tmp_path) -> None:
    """Missing --error/--review/--instruction should exit with code 1."""
    _setup_provider(temp_zero_dir)

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
    ])

    assert result.exit_code == 1
    assert "at least one of" in result.stdout.lower() or "must provide" in result.stdout.lower()

def test_fix_command_review_file_not_found(temp_zero_dir, tmp_path) -> None:
    """Passing a non-existent --review file should exit with code 1."""
    _setup_provider(temp_zero_dir)

    target = tmp_path / "src.py"
    target.write_text("x = 1\n", encoding="utf-8")

    result = runner.invoke(app, [
        "fix",
        "--file", str(target),
        "--review", "nonexistent_review.md",
    ])

    assert result.exit_code == 1
    assert "not found" in result.stdout
