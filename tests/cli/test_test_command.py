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

async def mock_test_stream(*args, **kwargs):
    yield MockChunk("def add(a, b):\n    return a + b\n")

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
@patch("subprocess.run")
def test_test_command_heals_automatically(mock_subrun, mock_acompletion, temp_zero_dir, tmp_path, monkeypatch) -> None:
    _setup_provider(temp_zero_dir)
    mock_acompletion.side_effect = mock_test_stream
    
    monkeypatch.chdir(tmp_path)
    
    target = tmp_path / "math.py"
    target.write_text("def add(a, b):\n    return a - b\n") # bug! should be +
    
    # First execution fails, second succeeds
    fail_mock = MagicMock()
    fail_mock.returncode = 1
    fail_mock.stdout = 'File "math.py", line 2, in test_add\nAssertionError\n'
    fail_mock.stderr = ""
    
    success_mock = MagicMock()
    success_mock.returncode = 0
    success_mock.stdout = "All tests passed"
    success_mock.stderr = ""
    
    mock_subrun.side_effect = [fail_mock, success_mock]
    
    result = runner.invoke(app, [
        "test",
        "--command", "pytest",
        "--yes"
    ])
    
    assert result.exit_code == 0
    assert "Iteration 1" in result.stdout
    assert "Command succeeded" in result.stdout
    # Verify content was updated
    assert "+" in target.read_text()
