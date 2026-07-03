"""Abstract Base Class and LiteLLM foundation for all Zero Action AI providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
import litellm


class BaseProvider(ABC):
    """Abstract Base Class defining standard operations for AI Providers."""

    @abstractmethod
    def connect(self) -> bool:
        """Initialize the connection to the provider.

        Returns:
            bool: True if connection is successfully established, False otherwise.
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Perform a synchronous chat completion request.

        Args:
            messages: List of message dicts containing 'role' and 'content'.
            **kwargs: Extra parameters to pass to the completion call.

        Returns:
            str: The text content of the response.
        """
        pass

    @abstractmethod
    def stream(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Perform an asynchronous streaming chat completion request.

        Args:
            messages: List of message dicts containing 'role' and 'content'.
            **kwargs: Extra parameters to pass to the completion call.

        Yields:
            str: Chunked response text contents.
        """
        pass

    @abstractmethod
    def embeddings(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for a given text input.

        Args:
            text: The input text to embed.
            **kwargs: Extra parameters.

        Returns:
            List[float]: The generated embedding vector.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Perform a connection health check test.

        Returns:
            bool: True if the provider is active and healthy, False otherwise.
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Retrieve a list of supported models.

        Returns:
            List[str]: List of model name identifiers.
        """
        pass

    @abstractmethod
    def token_count(self, text: str, **kwargs: Any) -> int:
        """Calculate the number of tokens in the given text input.

        Args:
            text: The input text.
            **kwargs: Extra parameters.

        Returns:
            int: The calculated number of tokens.
        """
        pass


class LiteLLMProvider(BaseProvider):
    """Base class for LiteLLM-backed AI Providers, implementing default logic."""

    def __init__(self, api_key: Optional[str], base_url: Optional[str], model: str) -> None:
        """Initialize LiteLLM provider.

        Args:
            api_key: The API Key for authorization.
            base_url: The base URL endpoint.
            model: The default model identifier.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def connect(self) -> bool:
        """Initialize the connection to the provider.

        Returns:
            bool: True if model is set.
        """
        return bool(self.model)

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Perform a synchronous completions request."""
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                api_base=self.base_url,
                **kwargs
            )
            try:
                from zero.services.billing import log_tokens
                prompt_toks = response.usage.prompt_tokens
                completion_toks = response.usage.completion_tokens
                log_tokens(self.model, prompt_toks, completion_toks)
            except Exception:
                pass
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"LiteLLM completion error: {e}")

    async def stream(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Perform an asynchronous streaming completions request."""
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                api_base=self.base_url,
                stream=True,
                **kwargs
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            raise Exception(f"LiteLLM async streaming error: {e}")

    def embeddings(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for a given text input."""
        try:
            model = kwargs.pop("model", "text-embedding-ada-002")
            response = litellm.embedding(
                model=model,
                input=[text],
                api_key=self.api_key,
                api_base=self.base_url,
                **kwargs
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"LiteLLM embedding error: {e}")

    def health_check(self) -> bool:
        """Perform a connection health check test by running a minor chat call."""
        try:
            self.chat([{"role": "user", "content": "ping"}], max_tokens=1)
            return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Retrieve a list of supported models."""
        return [self.model]

    def token_count(self, text: str, **kwargs: Any) -> int:
        """Calculate the number of tokens in the given text input."""
        try:
            return litellm.token_counter(model=self.model, text=text)
        except Exception:
            # Fallback estimation
            return len(text) // 4
