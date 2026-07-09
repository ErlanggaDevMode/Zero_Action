"""CLI integration tests for the doc-gen command."""

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
    yield MockChunk("```markdown\n")
    yield MockChunk("# API Reference\n")
    yield MockChunk("## GET /users\n")
    yield MockChunk("Returns all users.\n")
    yield MockChunk("```")


@patch("litellm.acompletion")
def test_cli_doc_gen_success(mock_acompletion, tmp_path, temp_zero_dir) -> None:
    """Test that zero doc-gen creates the api.md file."""
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
    
    # Create a routing file to scan
    app_file = workspace / "app.py"
    app_file.write_text("@app.get('/users')\ndef get_users():\n    pass\n", encoding="utf-8")
    
    output_doc_file = workspace / "docs" / "api.md"
    
    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM streaming completion
        mock_acompletion.side_effect = mock_async_stream
        
        result = runner.invoke(app, [
            "doc-gen",
            "--output", "docs/api.md",
            "--yes"
        ])
        
        assert result.exit_code == 0
        assert "API Documentation Generator" in result.stdout
        assert "Successfully generated API docs" in result.stdout
        
        assert output_doc_file.exists()
        assert "# API Reference" in output_doc_file.read_text(encoding="utf-8")
    finally:
        os.chdir(old_cwd)
