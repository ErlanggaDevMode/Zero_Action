"""Unit tests for configuration service parsing, validation, and serialization."""

import os
from pathlib import Path
import pytest
from zero.services.config import load_config
from zero.core.exceptions import ConfigError


def test_config_initialization(temp_zero_dir: Path) -> None:
    """Test that default config files are generated when loading config from an empty dir."""
    config = load_config(temp_zero_dir)

    # Verify files created
    assert (temp_zero_dir / "config.toml").exists()
    assert (temp_zero_dir / "providers.toml").exists()
    assert (temp_zero_dir / "settings.toml").exists()

    # Verify default values loaded
    assert config.app.debug is False
    assert config.app.verbose is False
    assert config.settings.theme == "dark"
    assert config.provider.active_provider == ""


def test_config_loads_existing_files(temp_zero_dir: Path) -> None:
    """Test that config loads custom values from existing TOML files."""
    # Write custom configurations
    with open(temp_zero_dir / "config.toml", "w", encoding="utf-8") as f:
        f.write("[app]\ndebug = true\n")

    with open(temp_zero_dir / "providers.toml", "w", encoding="utf-8") as f:
        f.write("[provider]\nactive_provider = \"ollama\"\n")

    with open(temp_zero_dir / "settings.toml", "w", encoding="utf-8") as f:
        f.write("[settings]\ntheme = \"light\"\n")

    config = load_config(temp_zero_dir)

    assert config.app.debug is True
    assert config.provider.active_provider == "ollama"
    assert config.settings.theme == "light"


def test_config_environment_override(temp_zero_dir: Path) -> None:
    """Test that environment variables successfully override config file parameters."""
    os.environ["ZERO_APP__DEBUG"] = "True"
    os.environ["ZERO_SETTINGS__THEME"] = "custom-theme"

    try:
        config = load_config(temp_zero_dir)
        assert config.app.debug is True
        assert config.settings.theme == "custom-theme"
    finally:
        os.environ.pop("ZERO_APP__DEBUG", None)
        os.environ.pop("ZERO_SETTINGS__THEME", None)


def test_config_invalid_toml_raises_error(temp_zero_dir: Path) -> None:
    """Test that malformed TOML raises ConfigError."""
    # Write invalid TOML
    with open(temp_zero_dir / "config.toml", "w", encoding="utf-8") as f:
        f.write("[app\ndebug = true")  # Missing bracket

    with pytest.raises(ConfigError) as exc_info:
        load_config(temp_zero_dir)

    assert "Malformed TOML" in str(exc_info.value)
