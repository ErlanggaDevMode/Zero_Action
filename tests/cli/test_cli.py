"""CLI Layer integration tests using Typer CliRunner."""

from typer.testing import CliRunner
from zero.cli.app import app


runner = CliRunner()


def test_cli_help(temp_zero_dir) -> None:
    """Test that CLI help command prints documentation and exits successfully."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Zero Action" in result.stdout
    assert "verify" in result.stdout


def test_cli_verify(temp_zero_dir) -> None:
    """Test that the verify command runs and logs configuration/environment data."""
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "Zero Action CLI Foundation is fully functional!" in result.stdout
    assert "Theme Setting: dark" in result.stdout
    assert "Debug Mode: False" in result.stdout
