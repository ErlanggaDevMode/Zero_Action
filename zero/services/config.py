"""Configuration service for Zero Action.

Loads settings from files in ~/.zero/ directory, supports environment variable overrides,
and provides schema validation models for all 10 supported AI providers.
"""

import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from zero.core.exceptions import ConfigError

# ==========================================
# Individual Provider Validation Models
# ==========================================

class OpenAIProviderConfig(BaseModel):
    """OpenAI connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"


class AnthropicProviderConfig(BaseModel):
    """Anthropic connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://api.anthropic.com/v1"
    model: str = "claude-3-5-sonnet-20241022"


class GeminiProviderConfig(BaseModel):
    """Google Gemini connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    model: str = "gemini-1.5-pro"


class OpenRouterProviderConfig(BaseModel):
    """OpenRouter connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "meta-llama/llama-3-70b-instruct"


class OllamaProviderConfig(BaseModel):
    """Ollama local model connection settings."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3"


class GroqProviderConfig(BaseModel):
    """Groq connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama3-70b-8192"


class AzureProviderConfig(BaseModel):
    """Azure OpenAI connection settings."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: str = "2024-02-15-preview"
    model: Optional[str] = None  # deployment name


class DeepSeekProviderConfig(BaseModel):
    """DeepSeek connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"


class MistralProviderConfig(BaseModel):
    """Mistral AI connection settings."""
    api_key: Optional[str] = None
    base_url: str = "https://api.mistral.ai/v1"
    model: str = "mistral-large-latest"


class CompatibleProviderConfig(BaseModel):
    """Generic OpenAI-Compatible endpoint connection settings."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


# ==========================================
# Consolidated Schema Models
# ==========================================

class AppConfig(BaseModel):
    """CLI Application settings."""
    debug: bool = False
    verbose: bool = False


class ProviderConfig(BaseModel):
    """Consolidated AI Provider connection and state settings."""
    active_provider: str = ""
    
    # Supported providers settings
    openai: OpenAIProviderConfig = Field(default_factory=OpenAIProviderConfig)
    anthropic: AnthropicProviderConfig = Field(default_factory=AnthropicProviderConfig)
    gemini: GeminiProviderConfig = Field(default_factory=GeminiProviderConfig)
    openrouter: OpenRouterProviderConfig = Field(default_factory=OpenRouterProviderConfig)
    ollama: OllamaProviderConfig = Field(default_factory=OllamaProviderConfig)
    groq: GroqProviderConfig = Field(default_factory=GroqProviderConfig)
    azure: AzureProviderConfig = Field(default_factory=AzureProviderConfig)
    deepseek: DeepSeekProviderConfig = Field(default_factory=DeepSeekProviderConfig)
    mistral: MistralProviderConfig = Field(default_factory=MistralProviderConfig)
    compatible: CompatibleProviderConfig = Field(default_factory=CompatibleProviderConfig)


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


# ==========================================
# Serialization & IO Helpers
# ==========================================

def dict_to_toml(d: Dict[str, Any], prefix: str = "") -> str:
    """Recursively serialize a dictionary to TOML format.

    Args:
        d: The dictionary to serialize.
        prefix: Path prefix representing nested levels.

    Returns:
        str: Serialized TOML content.
    """
    lines = []
    
    # 1. Output flat key-value fields first
    for k, v in d.items():
        if not isinstance(v, dict):
            if isinstance(v, bool):
                lines.append(f"{k} = {str(v).lower()}")
            elif isinstance(v, (int, float)):
                lines.append(f"{k} = {v}")
            elif v is None:
                lines.append(f"{k} = \"\"")
            else:
                escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f"{k} = \"{escaped}\"")

    # 2. Output sub-dictionaries as nested tables
    for k, v in d.items():
        if isinstance(v, dict):
            table_name = f"{prefix}.{k}" if prefix else k
            lines.append(f"\n[{table_name}]")
            sub_toml = dict_to_toml(v, prefix=table_name)
            if sub_toml.strip():
                lines.append(sub_toml.strip())

    return "\n".join(lines) + "\n"


def save_config(settings: ZeroSettings, config_dir: Path) -> None:
    """Serialize and save configuration settings back to TOML files on disk.

    Args:
        settings: The consolidated ZeroSettings to write.
        config_dir: Path to directory where config files reside.

    Raises:
        ConfigError: If files cannot be written or serialized.
    """
    try:
        config_dir.mkdir(parents=True, exist_ok=True)

        app_dict = {"app": settings.app.model_dump()}
        with open(config_dir / "config.toml", "w", encoding="utf-8") as f:
            f.write(dict_to_toml(app_dict))

        settings_dict = {"settings": settings.settings.model_dump()}
        with open(config_dir / "settings.toml", "w", encoding="utf-8") as f:
            f.write(dict_to_toml(settings_dict))

        provider_dict = {"provider": settings.provider.model_dump()}
        with open(config_dir / "providers.toml", "w", encoding="utf-8") as f:
            f.write(dict_to_toml(provider_dict))

    except Exception as e:
        raise ConfigError(f"Failed to write configuration files: {e}") from e


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
                if len(parts) >= 2:
                    curr = merged_data
                    for p in parts[:-1]:
                        if p not in curr:
                            curr[p] = {}
                        elif not isinstance(curr[p], dict):
                            curr[p] = {}
                        curr = curr[p]

                    # Convert to basic types if possible
                    parsed_val: Any = env_val
                    if env_val.lower() in ("true", "yes", "1"):
                        parsed_val = True
                    elif env_val.lower() in ("false", "no", "0"):
                        parsed_val = False
                    elif env_val.isdigit():
                        parsed_val = int(env_val)

                    curr[parts[-1]] = parsed_val

        # Build and validate setting object
        try:
            return ZeroSettings(**merged_data)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"  - {loc}: {msg}")
            err_msg = "\n".join(errors)
            raise ConfigError(f"Configuration validation failed:\n{err_msg}") from e

    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Error loading settings from {config_dir}: {e}") from e
