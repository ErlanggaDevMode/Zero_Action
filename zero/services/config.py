"""Configuration service for Zero Action.

Loads settings from files in ~/.zero/ directory and supports environment variable overrides.
"""

import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from zero.core.exceptions import ConfigError

class AppConfig(BaseModel):
    """CLI Application settings."""
    debug: bool = False
    verbose: bool = False


class ProviderConfig(BaseModel):
    """AI Provider connection and state settings."""
    active_provider: Optional[str] = None
    providers: Dict[str, Any] = Field(default_factory=dict)


class GlobalSettings(BaseModel):
    """User preferences and global workspace configurations."""
    theme: str = "dark"


class ZeroSettings(BaseSettings):
    """Consolidated configuration object for Zero Action."""
    app: AppConfig = Field(default_factory=AppConfig)
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    settings: GlobalSettings = Field(default_factory=GlobalSettings)

    model_config = SettingsConfigDict(
        env_prefix="ZERO_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )


def load_config(config_dir: Optional[Path] = None) -> ZeroSettings:
    """Load configuration from files in the specified directory, defaulting to ~/.zero.

    If directory or config files are missing, they are automatically initialized with defaults.

    Args:
        config_dir: Path to directory containing configurations.

    Returns:
        ZeroSettings: Validated configuration object.

    Raises:
        ConfigError: If files cannot be read, are malformed, or violate validation.
    """
    if config_dir is None:
        env_home = os.environ.get("ZERO_HOME")
        if env_home:
            config_dir = Path(env_home)
        else:
            config_dir = Path.home() / ".zero"

    try:
        # Create directory if it does not exist
        config_dir.mkdir(parents=True, exist_ok=True)

        app_path = config_dir / "config.toml"
        providers_path = config_dir / "providers.toml"
        settings_path = config_dir / "settings.toml"

        # Initialize defaults if files do not exist
        if not app_path.exists():
            with open(app_path, "w", encoding="utf-8") as f:
                f.write("[app]\ndebug = false\nverbose = false\n")

        if not providers_path.exists():
            with open(providers_path, "w", encoding="utf-8") as f:
                f.write("[provider]\nactive_provider = \"\"\n")

        if not settings_path.exists():
            with open(settings_path, "w", encoding="utf-8") as f:
                f.write("[settings]\ntheme = \"dark\"\n")

        # Read configurations from files
        merged_data: Dict[str, Any] = {}

        # Load app config
        try:
            with open(app_path, "rb") as f:
                data = tomllib.load(f)
                merged_data["app"] = data.get("app", data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Malformed TOML in {app_path}: {e}") from e

        # Load provider config
        try:
            with open(providers_path, "rb") as f:
                data = tomllib.load(f)
                merged_data["provider"] = data.get("provider", data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Malformed TOML in {providers_path}: {e}") from e

        # Load global settings
        try:
            with open(settings_path, "rb") as f:
                data = tomllib.load(f)
                merged_data["settings"] = data.get("settings", data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Malformed TOML in {settings_path}: {e}") from e

        # Load .env variables to environment (will be picked up by BaseSettings)
        from dotenv import load_dotenv
        load_dotenv()

        # Merge environment overrides into merged_data so they take precedence over TOML values
        for env_key, env_val in os.environ.items():
            if env_key.startswith("ZERO_"):
                parts = env_key[5:].lower().split("__")
                if len(parts) == 2:
                    section, option = parts
                    if section not in merged_data:
                        merged_data[section] = {}

                    # Convert to basic types if possible
                    parsed_val: Any = env_val
                    if env_val.lower() in ("true", "yes", "1"):
                        parsed_val = True
                    elif env_val.lower() in ("false", "no", "0"):
                        parsed_val = False
                    elif env_val.isdigit():
                        parsed_val = int(env_val)

                    merged_data[section][option] = parsed_val

        # Build setting object
        return ZeroSettings(**merged_data)

    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Error loading settings from {config_dir}: {e}") from e
