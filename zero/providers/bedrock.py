"""AWS Bedrock AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import BedrockProviderConfig


class BedrockProvider(LiteLLMProvider):
    """AWS Bedrock AI Provider wrapper using LiteLLM."""

    def __init__(self, config: BedrockProviderConfig) -> None:
        super().__init__(
            api_key=None,
            base_url=None,
            model=config.model,
        )
