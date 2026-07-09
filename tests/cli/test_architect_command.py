from unittest.mock import patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

# Mock chunk classes for LiteLLM streaming
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
    yield MockChunk("# Architecture Design: Test Project\n")
    yield MockChunk("## 1. Directory Structure\n")
    yield MockChunk("Mocked architecture output contents")

@patch("litellm.acompletion")
def test_architect_command_success(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    # 1. Setup active provider in settings/TOML
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    
    mock_acompletion.side_effect = mock_async_stream
    
    # 2. Invoke architect command with output path set to temporary directory
    out_file = tmp_path / "docs" / "architecture.md"
    result = runner.invoke(app, [
        "architect",
        "--requirements", "Design a CLI planning tool",
        "--output", str(out_file)
    ])
    
    # 3. Verify execution details
    assert result.exit_code == 0
    assert "Zero Action Architect" in result.stdout
    assert "Architectural Design Complete" in result.stdout
    
    # Verify file is written
    assert out_file.exists()
    file_content = out_file.read_text(encoding="utf-8")
    assert "# Architecture Design: Test Project" in file_content
    assert "Mocked architecture output contents" in file_content
