"""CLI integration tests for the benchmark command."""

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
    yield MockChunk("Hello")
    yield MockChunk(" World")


@patch("litellm.acompletion")
def test_cli_benchmark_success(mock_acompletion, tmp_path, temp_zero_dir) -> None:
    """Test that zero benchmark runs successfully and displays results."""
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

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM streaming completion
        mock_acompletion.side_effect = mock_async_stream
        
        result = runner.invoke(app, [
            "benchmark",
            "--prompt", "test prompt"
        ])
        
        assert result.exit_code == 0
        assert "Performance Benchmark" in result.stdout
        assert "Time to First Token" in result.stdout
        assert "Throughput" in result.stdout
    finally:
        os.chdir(old_cwd)
