"""Unit tests for newly added AI Providers (Nvidia, Alibaba, Bedrock, Vertex, OpenCode)."""

from unittest.mock import MagicMock, patch
from zero.providers.manager import ProviderManager
from zero.providers.nvidia import NvidiaProvider
from zero.providers.alibaba import AlibabaProvider
from zero.providers.bedrock import BedrockProvider
from zero.providers.vertex import VertexProvider
from zero.providers.opencode import OpenCodeProvider
from zero.services.config import load_config


def test_provider_manager_resolves_new_providers(temp_zero_dir) -> None:
    """Test that ProviderManager correctly resolves and instantiates the new providers."""
    config = load_config(temp_zero_dir)
    manager = ProviderManager(config)

    # Nvidia
    config.provider.active_provider = "nvidia"
    nvidia = manager.get_provider()
    assert isinstance(nvidia, NvidiaProvider)
    assert nvidia.model == "meta/llama3-70b-instruct"

    # Alibaba
    config.provider.active_provider = "alibaba"
    alibaba = manager.get_provider()
    assert isinstance(alibaba, AlibabaProvider)
    assert alibaba.model == "qwen-turbo"

    # Bedrock
    config.provider.active_provider = "bedrock"
    bedrock = manager.get_provider()
    assert isinstance(bedrock, BedrockProvider)
    assert bedrock.model == "anthropic.claude-3-sonnet-20240229-v1:0"

    # Vertex
    config.provider.active_provider = "vertex"
    vertex = manager.get_provider()
    assert isinstance(vertex, VertexProvider)
    assert vertex.model == "gemini-1.5-pro"

    # OpenCode
    config.provider.active_provider = "opencode"
    opencode = manager.get_provider()
    assert isinstance(opencode, OpenCodeProvider)
    assert opencode.model == "codellama/CodeLlama-34b-Instruct-hf"


@patch("litellm.completion")
def test_new_provider_chat_calls(mock_completion, temp_zero_dir) -> None:
    """Test that chat completions successfully trigger for new providers."""
    mock_choice = MagicMock()
    mock_choice.message.content = "New Provider Response"
    mock_completion.return_value.choices = [mock_choice]

    config = load_config(temp_zero_dir)
    manager = ProviderManager(config)
    messages = [{"role": "user", "content": "hi"}]

    # Nvidia NIM test
    nvidia = manager.get_provider("nvidia")
    res = nvidia.chat(messages)
    assert res == "New Provider Response"
    mock_completion.assert_called_with(
        model="meta/llama3-70b-instruct",
        messages=messages,
        api_key=None,
        api_base="https://integrate.api.nvidia.com/v1"
    )

    # Alibaba DashScope test
    alibaba = manager.get_provider("alibaba")
    res = alibaba.chat(messages)
    assert res == "New Provider Response"
    mock_completion.assert_called_with(
        model="qwen-turbo",
        messages=messages,
        api_key=None,
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
