from unittest.mock import patch
from typer.testing import CliRunner
from zero.cli.app import app
from zero.memory.manager import MemoryManager

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
    yield MockChunk("Mock ")
    yield MockChunk("AI ")
    yield MockChunk("response")

@patch("litellm.acompletion")
def test_ask_command_success(mock_acompletion, temp_zero_dir) -> None:
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
    
    # Mock LiteLLM async stream
    mock_acompletion.side_effect = mock_async_stream
    
    result = runner.invoke(app, ["ask", "What is Zero Action?"])
    
    assert result.exit_code == 0
    assert "Zero Action Ask" in result.stdout
    assert "Mock AI response" in result.stdout

@patch("litellm.acompletion")
def test_chat_command_success(mock_acompletion, temp_zero_dir) -> None:
    # 1. Setup active provider
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
    
    # 2. Mock terminal interaction loop (input "hello" then "exit")
    inputs = "hello\nexit\n"
    
    result = runner.invoke(app, ["chat"], input=inputs)
    
    assert result.exit_code == 0
    assert "Zero Action Chat" in result.stdout
    assert "Session:" in result.stdout
    assert "Mock AI response" in result.stdout
    assert "Chat session closed. Goodbye!" in result.stdout
    
    # 3. Verify conversation was saved in SQLite memory database
    db_path = temp_zero_dir / "memory.db"
    assert db_path.exists()
    
    memory = MemoryManager(db_path)
    sessions = memory.sessions.list_sessions()
    assert len(sessions) == 1
    
    messages = memory.sessions.get_messages(sessions[0]["id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Mock AI response"
