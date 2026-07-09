"""CLI integration tests for the update subcommand."""

from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("subprocess.run")
def test_cli_update_success(mock_run, temp_zero_dir) -> None:
    """Test that zero update command completes successfully with mocked subprocess commands."""
    # Setup mock subprocess outputs
    mock_response = MagicMock()
    mock_response.returncode = 0
    mock_response.stdout = "Already up to date."
    mock_run.return_value = mock_response

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "Starting Zero Action Auto-Update..." in result.stdout
    assert "Syncing and updating package installations..." in result.stdout
