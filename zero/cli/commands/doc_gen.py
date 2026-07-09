"""CLI subcommand to scan codebase routes and generate API documentation with AI assistance."""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.syntax import Syntax
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError
from zero.core.ui import stream_completion_with_timer
from zero.cli.commands.test import _strip_code_fences
from zero.cli.commands.schema import find_models_and_routes

def doc_gen(
    ctx: typer.Context,
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Custom output path for generated api.md"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve and write generated documentation without prompting"),
) -> None:
    """Scan project endpoints (FastAPI/Flask) and generate markdown API documentation."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error resolving AI provider:[/bold red] {e}")
        raise typer.Exit(code=1)

    cwd = Path.cwd().resolve()
    console.print(f"\n[bold green]Zero Action API Documentation Generator[/bold green] [dim]({provider.model})[/dim]")
    console.print(f"Scanning codebase inside [bold]{cwd}[/bold] for endpoints...")

    scan_results = find_models_and_routes(cwd)
    routes = scan_results.get("routes", [])

    if not routes:
        console.print("[yellow]No API routes (e.g. app.get, router.post, etc.) detected in Python files.[/yellow]")
        # We will still generate documentation based on general project analysis if the user proceeds
        user_confirmation = typer.confirm("Do you want to run a general doc generation based on all files anyway?", default=True)
        if not user_confirmation:
            raise typer.Exit(code=0)

    # Compile the code context of routing files
    scanned_context = []
    scanned_files = set(r["file"] for r in routes) if routes else []
    for rel_file in scanned_files:
        full_path = cwd / rel_file
        if full_path.exists():
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                scanned_context.append(f"--- File: {rel_file} ---\n{content}\n")
            except Exception:
                pass

    context_str = "\n".join(scanned_context) if scanned_context else "No source file context available."

    # Determine default output file
    if not output:
        docs_dir = cwd / "docs"
        docs_dir.mkdir(exist_ok=True)
        output_file = docs_dir / "api.md"
    else:
        output_file = Path(output).resolve()

    system_context = ai_service.get_system_prompt(Path.cwd())
    system_prompt = (
        f"{system_context}\n\n"
        "You are an expert Technical Writer. Generate a clean, complete, and beautiful API reference documentation "
        "in Markdown format for the scanned codebase endpoints. For each endpoint, detail the method, path, "
        "parameters, expected input/output format, and a brief description. Use a premium structure with a table of "
        "endpoints at the top. Return ONLY the markdown contents inside triple backticks (```markdown ... ```)."
    )

    user_prompt = (
        f"Generate markdown API documentation for this codebase.\n\n"
        f"**Routing Scanned Files & Context:**\n{context_str}\n\n"
        f"Please write the full markdown content to document all discovered endpoints."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    console.print("[yellow]Querying AI to generate markdown API documentation...[/yellow]")
    try:
        raw_response = asyncio.run(stream_completion_with_timer(provider, messages, console))
    except Exception as e:
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    generated_docs = _strip_code_fences(raw_response)
    if not generated_docs.strip():
        console.print("[bold red]AI returned empty response. API doc generation failed.[/bold red]")
        raise typer.Exit(code=1)

    console.print("\n[bold cyan]Preview of Generated API Documentation:[/bold cyan]")
    console.print(Syntax(generated_docs, "markdown", theme="monokai", line_numbers=True))

    # Confirm write
    if not yes:
        try:
            confirm = typer.confirm(f"Write API documentation to {output_file}?", default=True)
            if not confirm:
                console.print("[yellow]API documentation discarded.[/yellow]")
                raise typer.Exit(code=0)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]API doc generation aborted.[/yellow]")
            raise typer.Exit(code=1)

    # Write output
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(generated_docs, encoding="utf-8")
        console.print(f"[bold green]✓ Successfully generated API docs at: {output_file}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to write API docs to {output_file}:[/bold red] {e}")
        raise typer.Exit(code=1)
