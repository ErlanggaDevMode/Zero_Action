"""Provider manager to resolve and instantiate concrete provider implementations."""

from typing import Optional
from zero.core.exceptions import ConfigError
from zero.providers.base import BaseProvider
from zero.providers.registry import PROVIDER_CLASSES
from zero.services.config import ZeroSettings


class ProviderManager:
    """Manages AI Provider lifecycle, configurations resolution, and instantiation."""

    def __init__(self, settings: ZeroSettings) -> None:
        """Initialize the ProviderManager.

        Args:
            settings: Loaded ZeroSettings configuration settings.
        """
        self.settings = settings

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """Instantiate and return the requested provider.

        Defaults to the settings.provider.active_provider if no name is specified.

        Args:
            name: Optional string identifier of the provider.

        Returns:
            BaseProvider: The instantiated provider instance.

        Raises:
            ConfigError: If active provider is unset or unsupported.
        """
        provider_name = name or self.settings.provider.active_provider
        if not provider_name:
            raise ConfigError("No active AI provider configured.")

        normalized_name = provider_name.lower()
        provider_class = PROVIDER_CLASSES.get(normalized_name)
        if not provider_class:
            raise ConfigError(f"Unsupported AI provider: '{provider_name}'")

        # Extract settings attribute for this provider
        provider_settings = getattr(self.settings.provider, normalized_name, None)
        if provider_settings is None:
            raise ConfigError(f"No configurations found for provider: '{provider_name}'")

        return provider_class(provider_settings)  # type: ignore[call-arg]
