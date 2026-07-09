"""Azure OpenAI Provider implementation."""

from typing import Any, AsyncGenerator, Dict, List
from zero.providers.base import LiteLLMProvider
from zero.services.config import AzureProviderConfig


class AzureProvider(LiteLLMProvider):
    """Azure OpenAI Provider wrapper using LiteLLM."""

    def __init__(self, config: AzureProviderConfig) -> None:
        super().__init__(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model or "",
        )
        self.api_version = config.api_version

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Call Azure OpenAI completion with deployment names prefix."""
        model = self.model
        if model and not model.startswith("azure/"):
            model = f"azure/{model}"
        return super().chat(messages, model=model, api_version=self.api_version, **kwargs)

    async def stream(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Call Azure OpenAI streaming completion with deployment names prefix."""
        model = self.model
        if model and not model.startswith("azure/"):
            model = f"azure/{model}"
        async for chunk in super().stream(
            messages, model=model, api_version=self.api_version, **kwargs
        ):
            yield chunk
