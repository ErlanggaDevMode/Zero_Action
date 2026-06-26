"""CLI subcommand for interactive terminal conversation loops with memory tracking."""

import asyncio
import uuid
from pathlib import Path
import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from zero.services.ai import AIService
from zero.memory.manager import MemoryManager
from zero.core.exceptions import ConfigError
from zero.services.logging import logger

async def stream_chat_response(provider, messages, console: Console) -> str:
    """Stream chat completion response and return the full content."""
    response_text = ""
    with Live(Markdown(response_text), console=console, auto_refresh=False) as live:
        async for chunk in provider.stream(messages):
            response_text += chunk
            live.update(Markdown(response_text), refresh=True)
    console.print()
    return response_text

def chat(ctx: typer.Context) -> None:
    """Start an interactive chat session with context and memory tracking."""
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

    db_path = config_dir / "memory.db"
    memory = MemoryManager(db_path)
    session_id = str(uuid.uuid4())[:8]
    session_title = f"Chat Session {session_id}"
    
    try:
        memory.sessions.create_session(session_id, session_title)
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to initialize chat session in database: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not initialize session memory: {e}")
        raise typer.Exit(code=1)

    console.print(f"\n[bold green]Zero Action Chat[/bold green] [dim]({provider.model})[/dim]")
    console.print(f"Session: [cyan]{session_id}[/cyan] | Title: [dim]{session_title}[/dim]")
    console.print("[yellow]Type 'exit' or 'quit' to end the session.[/yellow]\n")

    while True:
        try:
            user_input = typer.prompt("You")
        except (typer.Abort, KeyboardInterrupt):
            console.print("\n[yellow]Chat session aborted.[/yellow]")
            break
            
        if user_input.strip().lower() in ("exit", "quit"):
            console.print("[green]Chat session closed. Goodbye![/green]")
            break
            
        if not user_input.strip():
            continue

        user_msg_id = str(uuid.uuid4())[:8]
        try:
            memory.sessions.add_message(
                message_id=user_msg_id,
                session_id=session_id,
                role="user",
                content=user_input,
                token_count=provider.token_count(user_input)
            )
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to save user message: {e}")

        history = memory.sessions.get_messages(session_id)
        system_prompt = ai_service.get_system_prompt(Path.cwd())
        
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        console.print("\n[bold green]Zero Action Assistant:[/bold green]")
        
        try:
            assistant_response = asyncio.run(stream_chat_response(provider, api_messages, console))
        except Exception as e:
            logger.bind(category="cli").error(f"Error during streaming chat completion: {e}")
            console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
            break

        assistant_msg_id = str(uuid.uuid4())[:8]
        try:
            memory.sessions.add_message(
                message_id=assistant_msg_id,
                session_id=session_id,
                role="assistant",
                content=assistant_response,
                token_count=provider.token_count(assistant_response)
            )
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to save assistant message: {e}")
            
        console.print()
