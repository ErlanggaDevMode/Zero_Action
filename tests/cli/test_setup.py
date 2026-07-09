"""CLI integration tests for the interactive setup wizard."""

import tomllib
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app


runner = CliRunner()


@patch("litellm.completion")
def test_setup_openai_success(mock_completion, temp_zero_dir) -> None:
    """Test standard successful setup flow for OpenAI provider."""
    # Mock completion for ping connection test success
    mock_completion.return_value = MagicMock()

    # Inputs: Provider, API Key, Base URL, Model, Configure backup providers (n), Clear backups (n)
    inputs = "openai\nsk-openai-key\nhttps://api.openai.com/v1\ngpt-4o\nn\nn\n"
    result = runner.invoke(app, ["setup"], input=inputs)

    assert result.exit_code == 0
    assert "Connection successful!" in result.stdout
    assert "Zero Action Setup Complete!" in result.stdout
    assert "active_provider" not in result.stderr  # check no error

    # Verify TOML saved to disk
    with open(temp_zero_dir / "providers.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["provider"]["active_provider"] == "openai"
    assert data["provider"]["openai"]["api_key"] == "sk-openai-key"
    assert data["provider"]["openai"]["model"] == "gpt-4o"


@patch("litellm.completion")
def test_setup_connection_failed_save_anyway(mock_completion, temp_zero_dir) -> None:
    """Test setup flow when connection check fails but user chooses to save settings anyway."""
    # Mock connection error
    mock_completion.side_effect = Exception("Connection Failed")

    # Inputs: Provider, API Key, Base URL, Model, Save anyway (y), Configure backup (n), Clear backups (n)
    inputs = "openai\nsk-fail-key\nhttps://api.openai.com/v1\ngpt-4o\ny\nn\nn\n"
    result = runner.invoke(app, ["setup"], input=inputs)

    assert result.exit_code == 0
    assert "Connection check failed" in result.stdout
    assert "Would you like to save this configuration anyway?" in result.stdout
    assert "Zero Action Setup Complete!" in result.stdout

    with open(temp_zero_dir / "providers.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["provider"]["active_provider"] == "openai"
    assert data["provider"]["openai"]["api_key"] == "sk-fail-key"


@patch("litellm.completion")
def test_setup_connection_failed_abort(mock_completion, temp_zero_dir) -> None:
    """Test setup flow when connection check fails and user chooses to abort setup."""
    mock_completion.side_effect = Exception("Connection Failed")

    # Inputs: Provider, API Key, Base URL, Model, Save anyway (n)
    inputs = "openai\nsk-fail-key\nhttps://api.openai.com/v1\ngpt-4o\nn\n"
    result = runner.invoke(app, ["setup"], input=inputs)

    assert result.exit_code == 1
    assert "Connection check failed" in result.stdout
    assert "Setup aborted" in result.stdout

    # Verify active_provider was not saved
    with open(temp_zero_dir / "providers.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["provider"]["active_provider"] == ""
