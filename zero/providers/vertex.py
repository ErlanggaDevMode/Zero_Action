"""GCP Vertex AI Provider implementation."""

from zero.providers.base import LiteLLMProvider
from zero.services.config import VertexProviderConfig


class VertexProvider(LiteLLMProvider):
    """GCP Vertex AI Provider wrapper using LiteLLM."""

    def __init__(self, config: VertexProviderConfig) -> None:
        super().__init__(
            api_key=None,
            base_url=None,
            model=config.model,
        )
