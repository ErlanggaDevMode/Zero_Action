"""CLI integration tests for the ask command with stdin piping."""

import os
from unittest.mock import patch
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
    yield MockChunk("Here is the explanation for the piped code:\n")
    yield MockChunk("It defines a simple function.")


@patch("litellm.acompletion")
@patch("sys.stdin")
def test_cli_ask_stdin_success(mock_stdin, mock_acompletion, tmp_path, temp_zero_dir) -> None:
    """Test that zero ask correctly reads from stdin when input is piped."""
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

    # Configure mock stdin to simulate piping
    mock_stdin.isatty.return_value = False
    mock_stdin.read.return_value = "def add(a, b): return a + b"

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        mock_acompletion.side_effect = mock_async_stream
        
        result = runner.invoke(app, ["ask", "explain this"])
        
        assert result.exit_code == 0
        assert "Zero Action Ask" in result.stdout
        assert "defines a simple function" in result.stdout
    finally:
        os.chdir(old_cwd)
