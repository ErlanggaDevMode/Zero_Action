"""CLI integration tests for the dashboard subcommand."""

from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("zero.cli.commands.dashboard.Application")
def test_cli_dashboard_success(mock_application_class, temp_zero_dir) -> None:
    """Test that zero dashboard subcommand configures the TUI and calls run."""
    # Setup active provider
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""", encoding="utf-8")

    mock_app_instance = MagicMock()
    mock_application_class.return_value = mock_app_instance

    result = runner.invoke(app, ["dashboard"])
    
    assert result.exit_code == 0
    assert mock_application_class.called
    assert mock_app_instance.run.called
