"""Unit tests for AI Provider abstraction layer using LiteLLM mocks."""

from unittest.mock import MagicMock, patch
import pytest
from zero.providers.manager import ProviderManager
from zero.providers.openai import OpenAIProvider
from zero.providers.anthropic import AnthropicProvider
from zero.services.config import load_config


def test_provider_manager_resolves_and_instantiates(temp_zero_dir) -> None:
    """Test that ProviderManager correctly resolves and instantiates active providers."""
    # Test unconfigured active provider
    config = load_config(temp_zero_dir)
    manager = ProviderManager(config)
    with pytest.raises(Exception) as exc:
        manager.get_provider()
    assert "No active AI provider configured" in str(exc.value)

    # Test resolved active provider
    config.provider.active_provider = "openai"
    provider = manager.get_provider()
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-4o"

    # Test explicit retrieval by name parameter
    anthropic_provider = manager.get_provider("anthropic")
    assert isinstance(anthropic_provider, AnthropicProvider)
    assert anthropic_provider.model == "claude-3-5-sonnet-20241022"


@patch("litellm.completion")
def test_provider_chat_call(mock_completion, temp_zero_dir) -> None:
    """Test that chat completions successfully trigger litellm.completion."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Hello from OpenAI Mock"
    mock_completion.return_value.choices = [mock_choice]

    config = load_config(temp_zero_dir)
    config.provider.active_provider = "openai"
    manager = ProviderManager(config)
    provider = manager.get_provider()

    messages = [{"role": "user", "content": "hello"}]
    res = provider.chat(messages)

    assert res == "Hello from OpenAI Mock"
    mock_completion.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        api_key=None,
        api_base="https://api.openai.com/v1"
    )


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_provider_stream_call(mock_acompletion, temp_zero_dir) -> None:
    """Test that async streaming correctly parses stream chunks."""
    mock_chunk1 = MagicMock()
    mock_chunk1.choices[0].delta.content = "Hello "
    mock_chunk2 = MagicMock()
    mock_chunk2.choices[0].delta.content = "world!"

    async def mock_async_gen(*args, **kwargs):
        yield mock_chunk1
        yield mock_chunk2

    mock_acompletion.return_value = mock_async_gen()

    config = load_config(temp_zero_dir)
    config.provider.active_provider = "openai"
    manager = ProviderManager(config)
    provider = manager.get_provider()

    messages = [{"role": "user", "content": "stream this"}]
    chunks = []
    async for chunk in provider.stream(messages):
        chunks.append(chunk)

    assert "".join(chunks) == "Hello world!"
    mock_acompletion.assert_called_once_with(
        model="gpt-4o",
        messages=messages,
        api_key=None,
        api_base="https://api.openai.com/v1",
        stream=True
    )


@patch("litellm.embedding")
def test_provider_embeddings_call(mock_embedding, temp_zero_dir) -> None:
    """Test that embedding requests correctly call litellm.embedding."""
    mock_data = MagicMock()
    mock_data.embedding = [0.1, 0.2, 0.3]
    mock_embedding.return_value.data = [mock_data]

    config = load_config(temp_zero_dir)
    config.provider.active_provider = "openai"
    manager = ProviderManager(config)
    provider = manager.get_provider()

    vec = provider.embeddings("hello")
    assert vec == [0.1, 0.2, 0.3]
    mock_embedding.assert_called_once_with(
        model="text-embedding-ada-002",
        input=["hello"],
        api_key=None,
        api_base="https://api.openai.com/v1"
    )


@patch("litellm.completion")
def test_provider_health_check(mock_completion, temp_zero_dir) -> None:
    """Test that health check handles connection diagnostics correctly."""
    mock_completion.return_value = MagicMock()

    config = load_config(temp_zero_dir)
    config.provider.active_provider = "openai"
    manager = ProviderManager(config)
    provider = manager.get_provider()

    # Success check
    assert provider.health_check() is True

    # Error check
    mock_completion.side_effect = Exception("Connection Failed")
    assert provider.health_check() is False
