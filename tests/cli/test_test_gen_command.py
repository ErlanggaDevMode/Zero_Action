"""CLI integration tests for the test-gen command."""

import os
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


class MockDelta:
    def __init__(self, content):
        self.content = content


class MockChoice:
    def __init__(self, content):
        self.delta = MockDelta(content)


class MockChunk:
    def __init__(self, content):
        self.choices = [MockChoice(content)]


async def mock_async_stream(*args, **kwargs):
    yield MockChunk("```python\n")
    yield MockChunk("def test_add():\n")
    yield MockChunk("    assert add(1, 2) == 3\n")
    yield MockChunk("```")


@patch("litellm.acompletion")
@patch("subprocess.run")
def test_cli_test_gen_success(mock_run, mock_acompletion, tmp_path, temp_zero_dir) -> None:
    """Test that zero test-gen creates a test file and passes validation checks."""
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
    
    target_file = workspace / "math_utils.py"
    target_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    
    output_test_file = workspace / "test_math_utils.py"
    
    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM streaming completion
        mock_acompletion.side_effect = mock_async_stream
        
        # Mock subprocess validations (ruff linter and pytest tests pass)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # ruff check
            MagicMock(returncode=0, stdout="", stderr="")  # pytest
        ]
        
        result = runner.invoke(app, [
            "test-gen",
            "math_utils.py",
            "--output", "test_math_utils.py",
            "--yes"
        ])
        
        print("STDOUT:", result.stdout)
        assert result.exit_code == 0
        assert "Zero Action Unit Test Generator" in result.stdout
        assert "Successfully wrote tests to" in result.stdout
        
        assert output_test_file.exists()
        assert "test_add" in output_test_file.read_text(encoding="utf-8")
    finally:
        os.chdir(old_cwd)
