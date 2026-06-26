"""Ollama AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import OllamaProviderConfig


class OllamaProvider(LiteLLMProvider):
    """Ollama AI Provider wrapper using LiteLLM."""

    def __init__(self, config: OllamaProviderConfig) -> None:
        super().__init__(
            api_key=None,
            base_url=config.base_url,
            model=config.model,
        )
