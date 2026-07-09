"""Groq AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import GroqProviderConfig


class GroqProvider(LiteLLMProvider):
    """Groq AI Provider wrapper using LiteLLM."""

    def __init__(self, config: GroqProviderConfig) -> None:
        super().__init__(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
        )
