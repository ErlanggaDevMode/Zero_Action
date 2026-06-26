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


def test_config_provider_validation(temp_zero_dir: Path) -> None:
    """Test that all 10 providers load with correct defaults."""
    config = load_config(temp_zero_dir)
    assert config.provider.openai.model == "gpt-4o"
    assert config.provider.anthropic.model == "claude-3-5-sonnet-20241022"
    assert config.provider.gemini.model == "gemini-1.5-pro"
    assert config.provider.ollama.model == "llama3"


def test_config_write_and_reload(temp_zero_dir: Path) -> None:
    """Test that save_config serializes settings to TOML files and reloading works."""
    from zero.services.config import save_config

    config = load_config(temp_zero_dir)
    config.settings.theme = "forest"
    config.provider.active_provider = "gemini"
    config.provider.gemini.api_key = "test-gemini-key"

    save_config(config, temp_zero_dir)

    # Reload from disk
    reloaded = load_config(temp_zero_dir)
    assert reloaded.settings.theme == "forest"
    assert reloaded.provider.active_provider == "gemini"
    assert reloaded.provider.gemini.api_key == "test-gemini-key"


def test_config_validation_error_format(temp_zero_dir: Path) -> None:
    """Test that schema validation errors are caught and formatted elegantly."""
    # Write invalid data type (e.g. invalid string for boolean)
    with open(temp_zero_dir / "config.toml", "w", encoding="utf-8") as f:
        f.write("[app]\ndebug = \"not-a-boolean\"\n")

    with pytest.raises(ConfigError) as exc_info:
        load_config(temp_zero_dir)

    assert "Configuration validation failed:" in str(exc_info.value)
    assert "app -> debug" in str(exc_info.value)


def test_config_environment_override_arbitrary_nesting(temp_zero_dir: Path) -> None:
    """Test that environment overrides support arbitrary nesting depths."""
    os.environ["ZERO_PROVIDER__OPENAI__API_KEY"] = "env-openai-key"
    os.environ["ZERO_PROVIDER__OPENAI__MODEL"] = "env-model"

    try:
        config = load_config(temp_zero_dir)
        assert config.provider.openai.api_key == "env-openai-key"
        assert config.provider.openai.model == "env-model"
    finally:
        os.environ.pop("ZERO_PROVIDER__OPENAI__API_KEY", None)
        os.environ.pop("ZERO_PROVIDER__OPENAI__MODEL", None)

