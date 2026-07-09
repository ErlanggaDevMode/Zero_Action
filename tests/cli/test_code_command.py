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

async def mock_async_stream_with_header(*args, **kwargs):
    yield MockChunk("File: gen/output.py\n")
    yield MockChunk("```python\n")
    yield MockChunk("def hello():\n    return 'world'\n")
    yield MockChunk("```")

async def mock_async_stream_without_header(*args, **kwargs):
    yield MockChunk("```python\n")
    yield MockChunk("def goodbye():\n    return 'everyone'\n")
    yield MockChunk("```")

@patch("litellm.acompletion")
def test_code_command_success_with_output_option(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    mock_acompletion.side_effect = mock_async_stream_without_header
    
    out_file = tmp_path / "src" / "test_out.py"
    result = runner.invoke(app, [
        "code",
        "--requirements", "Write test output file",
        "--output", str(out_file)
    ])
    
    assert result.exit_code == 0
    assert "Zero Action Coder" in result.stdout
    assert "Code Generation Complete" in result.stdout
    assert out_file.exists()
    assert "def goodbye():" in out_file.read_text(encoding="utf-8")

@patch("litellm.acompletion")
def test_code_command_parses_file_header(mock_acompletion, temp_zero_dir, tmp_path) -> None:
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    # Use an absolute path in the File: header so resolution is unambiguous
    out_file = tmp_path / "gen" / "output.py"
    # Normalize path to forward slashes for the AI response
    abs_path_str = str(out_file).replace("\\", "/")

    async def mock_stream_absolute_path(*args, **kwargs):
        yield MockChunk(f"File: {abs_path_str}\n")
        yield MockChunk("```python\n")
        yield MockChunk("def hello():\n    return 'world'\n")
        yield MockChunk("```")

    mock_acompletion.side_effect = mock_stream_absolute_path

    result = runner.invoke(app, [
        "code",
        "--requirements", "Write code based on headers"
    ])

    assert result.exit_code == 0
    assert out_file.exists()
    assert "def hello():" in out_file.read_text(encoding="utf-8")


@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_code_command_overwrite_yes(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    mock_acompletion.side_effect = mock_async_stream_without_header
    mock_confirm.return_value = True  # User says yes to overwrite
    
    out_file = tmp_path / "existing.py"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("original content", encoding="utf-8")
    
    result = runner.invoke(app, [
        "code",
        "--requirements", "overwrite it",
        "--output", str(out_file)
    ])
    
    assert result.exit_code == 0
    assert "Warning: File" in result.stdout
    assert "original content" not in out_file.read_text(encoding="utf-8")
    assert "def goodbye():" in out_file.read_text(encoding="utf-8")

@patch("litellm.acompletion")
@patch("rich.prompt.Confirm.ask")
def test_code_command_overwrite_no(mock_confirm, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    mock_acompletion.side_effect = mock_async_stream_without_header
    mock_confirm.return_value = False  # User says no to overwrite
    
    out_file = tmp_path / "existing.py"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("original content", encoding="utf-8")
    
    result = runner.invoke(app, [
        "code",
        "--requirements", "do not overwrite",
        "--output", str(out_file)
    ])
    
    assert result.exit_code == 0
    assert "Skipped writing file" in result.stdout
    assert out_file.read_text(encoding="utf-8") == "original content"

@patch("litellm.acompletion")
def test_code_command_spec_not_found(mock_acompletion, temp_zero_dir) -> None:
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    
    result = runner.invoke(app, [
        "code",
        "--spec", "non_existent_spec.md"
    ])
    
    assert result.exit_code == 1
    assert "Specification file 'non_existent_spec.md' not found." in result.stdout

@patch("litellm.acompletion")
@patch("rich.prompt.Prompt.ask")
def test_code_command_loads_default_spec_files(mock_prompt, mock_acompletion, temp_zero_dir, tmp_path) -> None:
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""")
    mock_acompletion.side_effect = mock_async_stream_without_header
    mock_prompt.return_value = "Generate code"
    
    # We create docs/prd.md in the current working directory mocked via Path.cwd
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "prd.md").write_text("This is the PRD specifications", encoding="utf-8")
    
    out_file = tmp_path / "out.py"
    
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        result = runner.invoke(app, [
            "code",
            "--output", str(out_file)
        ])
        
    assert result.exit_code == 0
    assert "Loaded specification context from: docs/prd.md" in result.stdout
