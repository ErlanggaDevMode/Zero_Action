"""OpenAI-Compatible Generic Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import CompatibleProviderConfig


class CompatibleProvider(LiteLLMProvider):
    """Generic OpenAI-Compatible Provider wrapper using LiteLLM."""

    def __init__(self, config: CompatibleProviderConfig) -> None:
        super().__init__(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model or "",
        )
