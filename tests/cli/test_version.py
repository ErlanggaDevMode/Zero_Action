"""CLI integration tests for the version subcommand."""

from typer.testing import CliRunner
from zero.cli.app import app


runner = CliRunner()


def test_cli_version(temp_zero_dir) -> None:
    """Test that zero version command displays environment details and exits successfully."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Zero Action CLI System Environment" in result.stdout
    assert "CLI Version" in result.stdout
    assert "1.0.0" in result.stdout
    assert str(temp_zero_dir) in result.stdout
