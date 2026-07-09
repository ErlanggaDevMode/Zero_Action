"""Unit tests for testing automatic AI Provider fallback logic."""

import pytest
from unittest.mock import MagicMock, patch
from zero.providers.manager import ProviderManager, FallbackProviderWrapper
from zero.services.config import load_config


def test_fallback_provider_wrapper_sync_chat(temp_zero_dir) -> None:
    """Test that FallbackProviderWrapper falls back on connection errors in sync chat."""
    config = load_config(temp_zero_dir)
    config.provider.active_provider = "openai"
    config.provider.backup_providers = ["anthropic", "gemini"]

    # Configure mock objects for provider implementations
    openai_mock = MagicMock()
    openai_mock.model = "gpt-4o"
    openai_mock.chat.side_effect = Exception("OpenAI API rate limit exceeded")

    anthropic_mock = MagicMock()
    anthropic_mock.model = "claude-3-5-sonnet-20241022"
    anthropic_mock.chat.return_value = "Response from Anthropic Backup"

    manager = ProviderManager(config)

    # Mock get_concrete_provider to return our mock objects
    def mock_get_concrete(name: str):
        if name.lower() == "openai":
            return openai_mock
        elif name.lower() == "anthropic":
            return anthropic_mock
        raise ValueError("Unexpected provider")

    with patch.object(manager, "get_concrete_provider", side_effect=mock_get_concrete):
        provider = manager.get_provider()
        
        assert isinstance(provider, FallbackProviderWrapper)
        
        messages = [{"role": "user", "content": "hello"}]
        res = provider.chat(messages)
        
        # Verify response fallback was successful
        assert res == "Response from Anthropic Backup"
        
        # Verify active provider was updated in settings
        assert config.provider.active_provider == "anthropic"


@pytest.mark.asyncio
async def test_fallback_provider_wrapper_async_stream(temp_zero_dir) -> None:
    """Test that FallbackProviderWrapper falls back on connection errors during async stream."""
    config = load_config(temp_zero_dir)
    config.provider.active_provider = "openai"
    config.provider.backup_providers = ["anthropic"]

    # Configure mock stream failure on OpenAI
    async def openai_stream_fail(*args, **kwargs):
        raise ValueError("OpenAI Stream failed")
        yield "Never yielded"

    openai_mock = MagicMock()
    openai_mock.model = "gpt-4o"
    openai_mock.stream.side_effect = openai_stream_fail

    # Configure successful mock stream on Anthropic
    async def anthropic_stream_ok(*args, **kwargs):
        yield "Hello "
        yield "from "
        yield "Anthropic"

    anthropic_mock = MagicMock()
    anthropic_mock.model = "claude-3-5-sonnet-20241022"
    anthropic_mock.stream.side_effect = anthropic_stream_ok

    manager = ProviderManager(config)

    def mock_get_concrete(name: str):
        if name.lower() == "openai":
            return openai_mock
        elif name.lower() == "anthropic":
            return anthropic_mock
        raise ValueError("Unexpected provider")

    with patch.object(manager, "get_concrete_provider", side_effect=mock_get_concrete):
        provider = manager.get_provider()
        
        messages = [{"role": "user", "content": "stream"}]
        
        chunks = []
        async for chunk in provider.stream(messages):
            chunks.append(chunk)
            
        assert "".join(chunks) == "Hello from Anthropic"
        assert config.provider.active_provider == "anthropic"
