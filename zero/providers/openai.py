"""OpenAI AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import OpenAIProviderConfig


class OpenAIProvider(LiteLLMProvider):
    """OpenAI AI Provider wrapper using LiteLLM."""

    def __init__(self, config: OpenAIProviderConfig) -> None:
        super().__init__(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
        )
