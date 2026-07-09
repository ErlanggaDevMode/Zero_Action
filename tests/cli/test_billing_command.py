"""CLI integration tests for the billing subcommand."""

from typer.testing import CliRunner
from zero.cli.app import app


runner = CliRunner()


def test_cli_billing(temp_zero_dir) -> None:
    """Test that zero billing command displays the summary and exits successfully."""
    result = runner.invoke(app, ["billing"])
    assert result.exit_code == 0
    assert "Zero Action Billing & API Usage Dashboard" in result.stdout
    assert "Total Completion Calls" in result.stdout
    assert "Total Estimated Cost" in result.stdout
