"""CLI subcommand for interactive terminal conversation loops with memory tracking."""

import asyncio
import shlex
import uuid
from pathlib import Path
from typing import Any, Optional, cast
import typer


from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from zero.services.ai import AIService
from zero.memory.manager import MemoryManager
from zero.core.exceptions import ConfigError
from zero.services.logging import logger

# Command dispatch handlers will lazy-import their respective subcommands



async def stream_chat_response(provider, messages, console: Console) -> str:
    """Stream chat completion response and return the full content."""
    response_text = ""
    with Live(Markdown(response_text), console=console, auto_refresh=False) as live:
        async for chunk in provider.stream(messages):
            response_text += chunk
            live.update(Markdown(response_text), refresh=True)
    console.print()
    return response_text


def parse_slash_args(cmd_args: str) -> tuple[dict[str, str], str]:
    """Parse slash command arguments into options and remaining requirements text."""
    try:
        parts = shlex.split(cmd_args)
    except Exception:
        parts = cmd_args.split()

    opts = {}
    req_parts = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ("-o", "--output") and i + 1 < len(parts):
            opts["output"] = parts[i + 1]
            i += 2
        elif part in ("-s", "--spec") and i + 1 < len(parts):
            opts["spec"] = parts[i + 1]
            i += 2
        elif part in ("-f", "--file") and i + 1 < len(parts):
            opts["file"] = parts[i + 1]
            i += 2
        elif part in ("-d", "--dir") and i + 1 < len(parts):
            opts["dir"] = parts[i + 1]
            i += 2
        elif part in ("-e", "--error") and i + 1 < len(parts):
            opts["error"] = parts[i + 1]
            i += 2
        elif part in ("-r", "--review") and i + 1 < len(parts):
            opts["review"] = parts[i + 1]
            i += 2
        elif part in ("-i", "--instruction") and i + 1 < len(parts):
            opts["instruction"] = parts[i + 1]
            i += 2
        elif part == "--focus" and i + 1 < len(parts):
            opts["focus"] = parts[i + 1]
            i += 2
        else:
            req_parts.append(part)
            i += 1
    return opts, " ".join(req_parts)


def show_repl_help(console: Console) -> None:
    """Print the interactive REPL slash command help list."""
    table = Table(
        title="[bold green]Zero Action CLI REPL Help[/bold green]",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Command", style="bold white")
    table.add_column("Description", style="dim")

    table.add_row("/help", "Show this help menu")
    table.add_row("/clear", "Clear the terminal screen")
    table.add_row("/init", "Scan workspace directory for repository context cache")
    table.add_row("/setup", "Interactive provider configuration wizard")
    table.add_row(
        "/provider [list/switch/test/models]",
        "View, configure, or test AI providers",
    )
    table.add_row("/plan [requirements]", "AI-generate Product Requirement Document (PRD)")
    table.add_row("/architect [requirements]", "AI-generate Architecture design document")
    table.add_row("/code [requirements]", "AI-generate project files with overwrite protection")
    table.add_row(
        "/review [file/dir]",
        "AI-perform code reviews (security, performance, maintainability...)",
    )
    table.add_row("/fix [file] [error/instruction]", "Surgically patch files with diff verification")
    table.add_row(
        "/memory [subcommand]",
        "Manage saved conversations, ADR decisions, and knowledge base",
    )
    table.add_row("/config [show/set]", "Display or assign app configurations dynamically")
    table.add_row("/exit / /quit", "Quit the interactive loop")

    console.print(table)


def handle_provider_command(parts: list[str], cmd_args: str, ctx: typer.Context, console: Console) -> None:
    """Dispatch provider subcommands."""
    from zero.cli.commands.provider import (
        default_callback as provider_show,
        list_providers,
        add_provider,
        remove_provider,
        switch_provider,
        list_models as provider_models,
        test_provider,
    )
    if len(parts) == 1:
        provider_show(ctx)
    else:
        sub = parts[1].lower()
        if sub == "list":
            list_providers(ctx)
        elif sub == "add" and len(parts) > 2:
            add_provider(ctx, parts[2])
        elif sub == "remove" and len(parts) > 2:
            remove_provider(ctx, parts[2])
        elif sub == "switch" and len(parts) > 2:
            switch_provider(ctx, parts[2])
        elif sub == "models":
            prov = parts[2] if len(parts) > 2 else None
            provider_models(ctx, prov)
        elif sub == "test":
            prov = parts[2] if len(parts) > 2 else None
            test_provider(ctx, prov)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown provider subcommand: '{sub}'.")


def handle_memory_command(parts: list[str], cmd_args: str, ctx: typer.Context, console: Console) -> None:
    """Dispatch memory subcommands."""
    from zero.cli.commands.memory import (
        list_sessions,
        show_session,
        delete_session,
        add_decision,
        list_decisions,
        import_knowledge,
    )
    if len(parts) < 2:
        console.print("[bold red]Error:[/bold red] Missing memory subcommand (e.g. /memory list-decisions).")
        return
    sub = parts[1].lower()
    if sub == "list-sessions":
        list_sessions(ctx)
    elif sub == "show-session" and len(parts) > 2:
        show_session(ctx, parts[2])
    elif sub == "delete-session" and len(parts) > 2:
        delete_session(ctx, parts[2])
    elif sub == "add-decision":
        content = " ".join(parts[2:])
        add_decision(ctx, content)
    elif sub == "list-decisions":
        list_decisions(ctx)
    elif sub == "import-knowledge" and len(parts) > 2:
        import_knowledge(ctx, Path(parts[2]))
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown memory subcommand: '{sub}'.")


def handle_config_command(parts: list[str], cmd_args: str, ctx: typer.Context, console: Console) -> None:
    """Dispatch config subcommands."""
    from zero.cli.commands.config import show as config_show, set_value as config_set
    if len(parts) < 2:
        console.print("[bold red]Error:[/bold red] Missing config subcommand (e.g. /config show).")
        return
    sub = parts[1].lower()
    if sub == "show":
        config_show(ctx)
    elif sub == "set" and len(parts) > 3:
        config_set(ctx, parts[2], parts[3])
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown config subcommand: '{sub}'.")



def handle_slash_command(user_input: str, ctx: typer.Context, console: Console) -> bool:
    """Handle slash commands inside REPL. Returns True if REPL loop should exit."""
    try:
        parts = shlex.split(user_input)
    except Exception:
        parts = user_input.split()

    if not parts:
        return False

    cmd = parts[0].lower()
    cmd_args = user_input[len(cmd):].strip()

    if cmd in ("/exit", "/quit"):
        console.print("[green]Chat REPL session closed. Goodbye![/green]")
        return True

    if cmd == "/clear":
        console.clear()
        return False

    if cmd == "/help":
        show_repl_help(console)
        return False

    try:
        if cmd == "/init":
            from zero.cli.commands.init import init
            init(ctx)

        elif cmd == "/setup":
            from zero.cli.commands.setup import setup
            setup(ctx)

        elif cmd == "/provider":
            handle_provider_command(parts, cmd_args, ctx, console)

        elif cmd == "/plan":
            from zero.cli.commands.plan import plan
            opts, reqs = parse_slash_args(cmd_args)
            out_path = Path(opts["output"]) if "output" in opts else Path("docs/prd.md")
            plan(ctx, requirements=reqs if reqs else "", output=out_path)

        elif cmd == "/architect":
            from zero.cli.commands.architect import architect
            opts, reqs = parse_slash_args(cmd_args)
            out_path = Path(opts["output"]) if "output" in opts else Path("docs/architecture.md")
            architect(ctx, requirements=reqs if reqs else "", output=out_path)

        elif cmd == "/code":
            from zero.cli.commands.code import code
            opts, reqs = parse_slash_args(cmd_args)
            code_out_path: Optional[Path] = Path(opts["output"]) if "output" in opts else None
            spec_path: Optional[Path] = Path(opts["spec"]) if "spec" in opts else None
            code(ctx, requirements=reqs if reqs else "", output=cast(Any, code_out_path), spec=cast(Any, spec_path))

        elif cmd == "/review":
            from zero.cli.commands.review import review
            opts, reqs = parse_slash_args(cmd_args)
            file_val: Optional[Path] = None
            dir_val: Optional[Path] = None
            if reqs:
                target = Path(reqs.split()[0])
                if target.is_file():
                    file_val = target
                elif target.is_dir():
                    dir_val = target

            review_file: Optional[Path] = Path(opts["file"]) if "file" in opts else file_val
            review_dir: Optional[Path] = Path(opts["dir"]) if "dir" in opts else dir_val
            review_out_path: Optional[Path] = Path(opts["output"]) if "output" in opts else None
            focus_val = opts.get("focus", "security,performance,maintainability,scalability,readability")

            review(ctx, file=cast(Any, review_file), dir=cast(Any, review_dir), output=cast(Any, review_out_path), focus=focus_val)

        elif cmd == "/fix":
            from zero.cli.commands.fix import fix
            opts, reqs = parse_slash_args(cmd_args)
            req_list = reqs.split() if reqs else []

            fix_file_val: Optional[Path] = Path(opts["file"]) if "file" in opts else (Path(req_list[0]) if req_list else None)
            instr_val = opts.get("instruction") or (" ".join(req_list[1:]) if len(req_list) > 1 else None)
            review_val: Optional[Path] = Path(opts["review"]) if "review" in opts else None
            fix_out_path: Optional[Path] = Path(opts["output"]) if "output" in opts else None
            err_val = opts.get("error")

            fix(ctx, file=cast(Any, fix_file_val), error=err_val, review_report=cast(Any, review_val), instruction=instr_val, output=cast(Any, fix_out_path))

        elif cmd == "/memory":
            handle_memory_command(parts, cmd_args, ctx, console)

        elif cmd == "/config":
            handle_config_command(parts, cmd_args, ctx, console)


        else:
            console.print(
                f"[bold red]Error:[/bold red] Unknown slash command: '{cmd}'. "
                f"Type [bold cyan]/help[/bold cyan] for a list of commands."
            )

    except typer.Exit:
        pass
    except typer.Abort:
        console.print("\n[yellow]Command aborted.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Command error:[/bold red] {e}")

    return False


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

    active_provider = settings.provider.active_provider or "none"
    provider_defaults = getattr(settings.provider, active_provider) if active_provider != "none" else None
    active_model = provider_defaults.model if provider_defaults else "none"
    cwd_name = Path.cwd().name

    console.print(
        Panel(
            f"Active Provider: [bold cyan]{active_provider}[/bold cyan] | "
            f"Model: [bold cyan]{active_model}[/bold cyan]\n"
            f"Workspace Directory: [white]{Path.cwd()}[/white]\n"
            f"Session ID: [cyan]{session_id}[/cyan]\n\n"
            f"Type [bold green]/help[/bold green] to list commands. "
            f"Type [bold green]/exit[/bold green] or [bold green]/quit[/bold green] to end the session.",
            title="[bold green]Zero Action Chat Console[/bold green]",
            border_style="green",
        )
    )

    while True:
        try:
            # Build Claude Code styled prompt
            prompt_str = (
                f"[bold green]zero-action[/bold green] "
                rf"\[[cyan]{active_provider}/{active_model}[/cyan]\] "
                f"[blue]{cwd_name}[/blue] >"
            )

            user_input = Prompt.ask(prompt_str)
        except (KeyboardInterrupt, EOFError, typer.Abort):
            console.print("\n[yellow]REPL session terminated.[/yellow]")
            break

        if not user_input.strip():
            continue

        # Check for slash commands
        if user_input.strip().startswith("/"):
            should_exit = handle_slash_command(user_input.strip(), ctx, console)
            if should_exit:
                break
            continue

        # Standard conversation path
        user_msg_id = str(uuid.uuid4())[:8]
        try:
            memory.sessions.add_message(
                message_id=user_msg_id,
                session_id=session_id,
                role="user",
                content=user_input,
                token_count=provider.token_count(user_input),
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
                token_count=provider.token_count(assistant_response),
            )
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to save assistant message: {e}")

        console.print()
