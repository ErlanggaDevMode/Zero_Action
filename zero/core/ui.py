"""Shared terminal UI components and dynamic display utilities."""

import asyncio
import time
from typing import Any
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner


async def stream_completion_with_timer(provider, messages, console: Console, **kwargs: Any) -> str:
    """Stream AI completion response while showing a real-time thinking spinner and elapsed timer.

    Args:
        provider: The resolved AI provider instance.
        messages: The chat messages history to send.
        console: The Rich Console to print output to.
        **kwargs: Optional query arguments to pass to provider.stream.

    Returns:
        The full string response from the AI provider.
    """
    start_time = time.time()
    response_text = ""
    first_token_received = False

    async def update_timer(live_instance: Live) -> None:
        while not first_token_received:
            elapsed = time.time() - start_time
            spinner = Spinner("dots", text=f"Thinking ({elapsed:.1f}s)...", style="cyan")
            live_instance.update(spinner, refresh=True)
            await asyncio.sleep(0.1)

    # Initial thinking status spinner
    with Live(Spinner("dots", text="Thinking (0.0s)...", style="cyan"), console=console, auto_refresh=False) as live:
        timer_task = asyncio.create_task(update_timer(live))
        try:
            async for chunk in provider.stream(messages, **kwargs):
                if not first_token_received:
                    first_token_received = True
                    timer_task.cancel()
                response_text += chunk
                live.update(Markdown(response_text), refresh=True)
        finally:
            if not timer_task.done():
                timer_task.cancel()

    total_time = time.time() - start_time
    console.print(f"[dim]Completed in {total_time:.1f}s[/dim]\n")
    try:
        from zero.services.billing import log_tokens
        prompt_text = "".join(m.get("content", "") for m in messages if isinstance(m, dict))
        prompt_tokens = provider.token_count(prompt_text)
        completion_tokens = provider.token_count(response_text)
        log_tokens(provider.model, prompt_tokens, completion_tokens)
    except Exception:
        pass
    return response_text
