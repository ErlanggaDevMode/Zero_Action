import os
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator
from zero.core.exceptions import ConfigError
from zero.providers.base import BaseProvider
from zero.providers.registry import PROVIDER_CLASSES
from zero.services.config import ZeroSettings
from rich.console import Console


class FallbackProviderWrapper(BaseProvider):
    """Wrapper that delegates calls to active provider and switches to backup providers on failure."""

    def __init__(self, active_provider: BaseProvider, backup_names: List[str], manager: "ProviderManager") -> None:
        self.active_provider = active_provider
        self.backup_names = backup_names
        self.manager = manager
        # Mirror attributes of active provider
        self.model = getattr(active_provider, "model", "default-model")
        self.api_key = getattr(active_provider, "api_key", None)
        self.base_url = getattr(active_provider, "base_url", None)
        if hasattr(active_provider, "is_custom_compatible"):
            self.is_custom_compatible = getattr(active_provider, "is_custom_compatible")

    def connect(self) -> bool:
        return self.active_provider.connect()

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        try:
            return self.active_provider.chat(messages, **kwargs)
        except Exception as e:
            if not self.backup_names:
                raise e
            next_backup = self.backup_names[0]
            Console().print(f"[yellow]⚠️ Connection to active provider failed: {e}. Automatically switching to backup provider: '{next_backup}'...[/yellow]")
            
            # Switch active provider in settings
            self.manager.settings.provider.active_provider = next_backup
            from zero.services.config import save_config
            config_dir = Path(os.environ.get("ZERO_CONFIG_DIR") or Path.home() / ".zero")
            try:
                save_config(self.manager.settings, config_dir)
            except Exception:
                pass
                
            backup_instance = self.manager.get_concrete_provider(next_backup)
            wrapped_backup = FallbackProviderWrapper(backup_instance, self.backup_names[1:], self.manager)
            return wrapped_backup.chat(messages, **kwargs)

    async def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> AsyncGenerator[str, None]:
        try:
            async for chunk in self.active_provider.stream(messages, **kwargs):
                yield chunk
        except Exception as e:
            if not self.backup_names:
                raise e
            next_backup = self.backup_names[0]
            Console().print(f"[yellow]⚠️ Connection to active provider failed: {e}. Automatically switching to backup provider: '{next_backup}'...[/yellow]")
            
            self.manager.settings.provider.active_provider = next_backup
            from zero.services.config import save_config
            config_dir = Path(os.environ.get("ZERO_CONFIG_DIR") or Path.home() / ".zero")
            try:
                save_config(self.manager.settings, config_dir)
            except Exception:
                pass
                
            backup_instance = self.manager.get_concrete_provider(next_backup)
            wrapped_backup = FallbackProviderWrapper(backup_instance, self.backup_names[1:], self.manager)
            async for chunk in wrapped_backup.stream(messages, **kwargs):
                yield chunk

    def embeddings(self, text: str, **kwargs: Any) -> List[float]:
        try:
            return self.active_provider.embeddings(text, **kwargs)
        except Exception as e:
            if not self.backup_names:
                raise e
            next_backup = self.backup_names[0]
            backup_instance = self.manager.get_concrete_provider(next_backup)
            wrapped_backup = FallbackProviderWrapper(backup_instance, self.backup_names[1:], self.manager)
            return wrapped_backup.embeddings(text, **kwargs)

    def health_check(self) -> bool:
        return self.active_provider.health_check()

    def list_models(self) -> List[str]:
        return self.active_provider.list_models()

    def token_count(self, text: str, **kwargs: Any) -> int:
        return self.active_provider.token_count(text, **kwargs)


class ProviderManager:
    """Manages AI Provider lifecycle, configurations resolution, and instantiation."""

    def __init__(self, settings: ZeroSettings) -> None:
        """Initialize the ProviderManager.

        Args:
            settings: Loaded ZeroSettings configuration settings.
        """
        self.settings = settings

    def get_concrete_provider(self, name: str) -> BaseProvider:
        """Instantiate and return raw unwrapped concrete provider."""
        normalized_name = name.lower()
        provider_class = PROVIDER_CLASSES.get(normalized_name)
        if not provider_class:
            raise ConfigError(f"Unsupported AI provider: '{name}'")

        provider_settings = getattr(self.settings.provider, normalized_name, None)
        if provider_settings is None:
            raise ConfigError(f"No configurations found for provider: '{name}'")

        return provider_class(provider_settings)  # type: ignore[call-arg]

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """Instantiate and return the requested provider (wrapped with backup fallback if active provider)."""
        provider_name = name or self.settings.provider.active_provider
        if not provider_name:
            raise ConfigError("No active AI provider configured.")

        concrete = self.get_concrete_provider(provider_name)

        if not name:
            backups = [b for b in self.settings.provider.backup_providers if b.lower() != provider_name.lower()]
            if backups:
                return FallbackProviderWrapper(concrete, backups, self)
        return concrete
