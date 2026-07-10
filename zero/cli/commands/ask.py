"""CLI subcommand for single-shot question asking to configured AI model (with piping support)."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from zero.services.logging import logger
from zero.core.ui import stream_completion_with_timer

def ask(
    ctx: typer.Context,
    question: Optional[str] = typer.Argument(None, help="The prompt/question to ask the AI model (or reads from stdin if piped)")
) -> None:
    """Ask a single-shot question to the active AI provider with workspace context."""
    from zero.services.ai import AIService
    from zero.core.exceptions import ConfigError

    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # 1. Read from stdin if piped
    stdin_content = ""
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read from stdin: {e}")

    if not question and not stdin_content:
        console.print("[bold red]Error:[/bold red] Missing question. Please provide a question or pipe content into stdin.")
        raise typer.Exit(code=1)

    # 2. Combine prompts
    if question and stdin_content:
        full_prompt = f"{question}\n\n[Piped Input]:\n{stdin_content}"
    elif question:
        full_prompt = question
    else:
        full_prompt = stdin_content

    # 3. Resolve AI provider
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        console.print("[yellow]Please run 'zero setup' first to configure your active provider.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error resolving AI provider:[/bold red] {e}")
        raise typer.Exit(code=1)

    system_prompt = ai_service.get_system_prompt(Path.cwd(), query=full_prompt)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_prompt}
    ]

    console.print(f"\n[bold green]Zero Action Ask[/bold green] [dim]({provider.model})[/dim]\n")
    try:
        asyncio.run(stream_completion_with_timer(provider, messages, console))
    except Exception as e:
        logger.bind(category="cli").error(f"Error during ask command completion: {e}")
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)
