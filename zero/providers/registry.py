"""Registry holding standard name bindings for all AI Provider classes."""

from typing import Dict, Type
from zero.providers.base import BaseProvider
from zero.providers.openai import OpenAIProvider
from zero.providers.anthropic import AnthropicProvider
from zero.providers.gemini import GeminiProvider
from zero.providers.openrouter import OpenRouterProvider
from zero.providers.ollama import OllamaProvider
from zero.providers.groq import GroqProvider
from zero.providers.azure import AzureProvider
from zero.providers.deepseek import DeepSeekProvider
from zero.providers.mistral import MistralProvider
from zero.providers.compatible import CompatibleProvider
from zero.providers.nvidia import NvidiaProvider
from zero.providers.alibaba import AlibabaProvider
from zero.providers.bedrock import BedrockProvider
from zero.providers.vertex import VertexProvider
from zero.providers.opencode import OpenCodeProvider

PROVIDER_CLASSES: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
    "groq": GroqProvider,
    "azure": AzureProvider,
    "deepseek": DeepSeekProvider,
    "mistral": MistralProvider,
    "compatible": CompatibleProvider,
    "nvidia": NvidiaProvider,
    "alibaba": AlibabaProvider,
    "bedrock": BedrockProvider,
    "vertex": VertexProvider,
    "opencode": OpenCodeProvider,
}
