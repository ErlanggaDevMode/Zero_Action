"""DeepSeek AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import DeepSeekProviderConfig


class DeepSeekProvider(LiteLLMProvider):
    """DeepSeek AI Provider wrapper using LiteLLM."""

    def __init__(self, config: DeepSeekProviderConfig) -> None:
        super().__init__(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            provider_name="deepseek",
        )
