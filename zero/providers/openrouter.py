"""OpenRouter AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import OpenRouterProviderConfig


class OpenRouterProvider(LiteLLMProvider):
    """OpenRouter AI Provider wrapper using LiteLLM."""

    def __init__(self, config: OpenRouterProviderConfig) -> None:
        super().__init__(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
        )
