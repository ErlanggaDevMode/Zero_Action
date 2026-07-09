"""CLI integration tests for configuration management subcommands."""

from pathlib import Path
import tomllib
from typer.testing import CliRunner
from zero.cli.app import app


runner = CliRunner()


def test_config_show(temp_zero_dir: Path) -> None:
    """Test that zero config show command renders the configuration tree."""
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "Zero Action Configurations" in result.stdout
    assert "App Settings" in result.stdout
    assert "Global Settings" in result.stdout
    assert "Provider Settings" in result.stdout


def test_config_set_success(temp_zero_dir: Path) -> None:
    """Test that zero config set command updates config fields and saves to TOML files."""
    # Test setting theme
    result = runner.invoke(app, ["config", "set", "settings.theme", "light"])
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert "settings.theme" in result.stdout
    assert "light" in result.stdout

    # Verify settings.toml contents on disk
    with open(temp_zero_dir / "settings.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["settings"]["theme"] == "light"

    # Test setting debug flag
    result = runner.invoke(app, ["config", "set", "app.debug", "true"])
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert "app.debug" in result.stdout
    assert "true" in result.stdout

    # Verify config.toml contents on disk
    with open(temp_zero_dir / "config.toml", "rb") as f:
        data = tomllib.load(f)
    assert data["app"]["debug"] is True


def test_config_set_invalid_field(temp_zero_dir: Path) -> None:
    """Test that zero config set command fails when referencing non-existent properties."""
    result = runner.invoke(app, ["config", "set", "settings.non_existent", "value"])
    assert result.exit_code == 1
    assert "Error" in result.stderr
    assert "non_existent" in result.stderr


def test_config_set_invalid_value_type(temp_zero_dir: Path) -> None:
    """Test that zero config set command validates data types."""
    result = runner.invoke(app, ["config", "set", "app.debug", "not-a-bool"])
    assert result.exit_code == 1
    assert "expects a boolean" in result.stderr
