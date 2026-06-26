"""Shell autocompletion helpers for CLI arguments and options."""

from typing import List


def autocomplete_providers(incomplete: str) -> List[str]:
    """Provide shell autocomplete suggestions for AI providers.

    Args:
        incomplete: The current partial input string.

    Returns:
        List[str]: List of matching provider strings.
    """
    providers = [
        "openai",
        "anthropic",
        "gemini",
        "openrouter",
        "ollama",
        "groq",
        "azure",
        "deepseek",
        "mistral",
        "compatible",
    ]
    return [p for p in providers if p.startswith(incomplete.lower())]
