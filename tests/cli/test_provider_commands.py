import tomllib
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

def test_provider_list_command(temp_zero_dir) -> None:
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
""")
    
    result = runner.invoke(app, ["provider", "list"])
    assert result.exit_code == 0
    assert "openai" in result.stdout
    assert "gemini" in result.stdout
    assert "Active" in result.stdout

def test_provider_switch_command(temp_zero_dir) -> None:
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
[provider.anthropic]
api_key = ""
""")
    
    result_fail = runner.invoke(app, ["provider", "switch", "anthropic"])
    assert result_fail.exit_code == 1
    assert "not configured" in result_fail.stdout
    
    result_ok = runner.invoke(app, ["provider", "switch", "ollama"])
    assert result_ok.exit_code == 0
    assert "switched to ollama" in result_ok.stdout
    
    with open(providers_toml, "rb") as f:
        data = tomllib.load(f)
    assert data["provider"]["active_provider"] == "ollama"

def test_provider_remove_command(temp_zero_dir) -> None:
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
""")
    
    result = runner.invoke(app, ["provider", "remove", "openai"], input="y\n")
    assert result.exit_code == 0
    assert "Cleared configurations" in result.stdout
    
    with open(providers_toml, "rb") as f:
        data = tomllib.load(f)
    assert data["provider"]["openai"]["api_key"] == ""
    assert data["provider"]["active_provider"] == ""

@patch("litellm.completion")
def test_provider_test_and_models_command(mock_completion, temp_zero_dir) -> None:
    mock_completion.return_value = MagicMock()
    
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
model = "gpt-4"
""")
    
    result_models = runner.invoke(app, ["provider", "models"])
    assert result_models.exit_code == 0
    assert "gpt-4" in result_models.stdout
    
    result_ping = runner.invoke(app, ["provider", "test"])
    assert result_ping.exit_code == 0
    assert "healthy and connected" in result_ping.stdout
