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
    yield MockChunk("# PRD: Test Project\n")
    yield MockChunk("## 1. Executive Summary\n")
    yield MockChunk("Mocked PRD output contents")

@patch("litellm.acompletion")
def test_plan_command_success(mock_acompletion, temp_zero_dir, tmp_path) -> None:
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
    
    # 2. Invoke plan command with output path set to temporary directory
    out_file = tmp_path / "docs" / "prd.md"
    result = runner.invoke(app, [
        "plan",
        "--requirements", "Design a CLI planning tool",
        "--output", str(out_file)
    ])
    
    # 3. Verify execution details
    assert result.exit_code == 0
    assert "Zero Action Planner" in result.stdout
    assert "Planning Complete" in result.stdout
    
    # Verify file is written
    assert out_file.exists()
    file_content = out_file.read_text(encoding="utf-8")
    assert "# PRD: Test Project" in file_content
    assert "Mocked PRD output contents" in file_content
