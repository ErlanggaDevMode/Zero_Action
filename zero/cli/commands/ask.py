"""CLI subcommand for single-shot question asking to configured AI model."""

import asyncio
from pathlib import Path
import typer
from rich.console import Console
from zero.services.logging import logger
from zero.core.ui import stream_completion_with_timer

def ask(
    ctx: typer.Context,
    question: str = typer.Argument(..., help="The prompt/question to ask the AI model")
) -> None:
    from zero.services.ai import AIService
    from zero.core.exceptions import ConfigError

    """Ask a single-shot question to the active AI provider with workspace context."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir
    
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

    system_prompt = ai_service.get_system_prompt(Path.cwd())
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    console.print(f"\n[bold green]Zero Action Ask[/bold green] [dim]({provider.model})[/dim]\n")
    try:
        asyncio.run(stream_completion_with_timer(provider, messages, console))
    except Exception as e:

        logger.bind(category="cli").error(f"Error during ask command completion: {e}")
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)
