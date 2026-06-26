"""CLI subcommand to perform AI-powered automated code fixing with diff preview and confirmation."""

import asyncio
import difflib
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.live import Live
from rich.markdown import Markdown
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError
from zero.services.logging import logger


async def stream_fix_response(provider, messages, console: Console) -> str:
    """Stream fixer response and return the full content."""
    response_text = ""
    with Live(Markdown(response_text), console=console, auto_refresh=False) as live:
        async for chunk in provider.stream(messages):
            response_text += chunk
            live.update(Markdown(response_text), refresh=True)
    console.print()
    return response_text


def _strip_code_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences if the AI accidentally includes them."""
    lines = text.splitlines()
    # Strip leading fence line (``` or ```python etc.)
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    # Strip trailing fence line
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _render_diff(original: str, fixed: str, filename: str, console: Console) -> None:
    """Render a unified diff between original and fixed content using Rich Syntax."""
    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"original/{filename}",
            tofile=f"fixed/{filename}",
            lineterm="",
        )
    )
    if not diff_lines:
        console.print("[yellow]No changes detected in the AI response.[/yellow]")
        return

    diff_text = "".join(diff_lines)
    console.print(
        Panel(
            Syntax(diff_text, "diff", theme="monokai", line_numbers=False),
            title="[bold cyan]Proposed Changes (Diff)[/bold cyan]",
            border_style="cyan",
            expand=True,
        )
    )


def fix(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file", "-f", help="Source file to fix"),
    error: Optional[str] = typer.Option(None, "--error", "-e", help="Error message, traceback, or problem description"),
    review_report: Optional[Path] = typer.Option(None, "--review", "-r", help="Path to a review report file (e.g. from 'zero review --output')"),
    instruction: Optional[str] = typer.Option(None, "--instruction", "-i", help="Free-form fix instruction"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write fixed code to this path (default: overwrite --file after confirmation)"),
) -> None:
    """Fix a source file using AI, preview the diff, and write only after confirmation."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # -- Provider setup -------------------------------------------------------
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

    # -- Validate --file exists -----------------------------------------------
    if not file.exists():
        console.print(f"[bold red]Error:[/bold red] File '{file}' not found.")
        raise typer.Exit(code=1)
    if not file.is_file():
        console.print(f"[bold red]Error:[/bold red] '{file}' is not a file.")
        raise typer.Exit(code=1)

    # -- Require at least one problem specifier -------------------------------
    if not error and not review_report and not instruction:
        console.print(
            "[bold red]Error:[/bold red] You must provide at least one of: "
            "[cyan]--error[/cyan], [cyan]--review[/cyan], or [cyan]--instruction[/cyan]."
        )
        raise typer.Exit(code=1)

    # -- Read source file -----------------------------------------------------
    try:
        original_content = file.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[bold red]Error reading '{file}':[/bold red] {e}")
        raise typer.Exit(code=1)

    # -- Load optional review report ------------------------------------------
    review_content = ""
    if review_report:
        if not review_report.exists():
            console.print(f"[bold red]Error:[/bold red] Review report '{review_report}' not found.")
            raise typer.Exit(code=1)
        try:
            review_content = review_report.read_text(encoding="utf-8")
            console.print(f"[green]ℹ[/green] Loaded review report from [dim]{review_report}[/dim].")
        except Exception as e:
            logger.warning(f"Failed to read review report: {e}")

    # -- Load fixer prompt instructions ---------------------------------------
    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "fixer.md"
    fixer_instructions = ""
    if prompt_file.exists():
        try:
            fixer_instructions = prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read fixer prompt template: {e}")

    if not fixer_instructions:
        fixer_instructions = (
            "You are a code fixer. Output ONLY the complete corrected source file. "
            "No explanations, no code fences. Preserve all unrelated logic."
        )

    # -- Build prompt messages ------------------------------------------------
    system_context = ai_service.get_system_prompt(Path.cwd())
    system_prompt = f"{system_context}\n\n{fixer_instructions}"

    problem_parts: list[str] = []
    if error:
        problem_parts.append(f"**Error / Problem:**\n{error}")
    if review_content:
        problem_parts.append(f"**Review Report:**\n{review_content}")
    if instruction:
        problem_parts.append(f"**Fix Instruction:**\n{instruction}")

    user_prompt = (
        f"Fix the following source file.\n\n"
        f"**File:** {file}\n\n"
        f"**Current Content:**\n```\n{original_content}\n```\n\n"
        + "\n\n".join(problem_parts)
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # -- Stream AI response ---------------------------------------------------
    console.print(f"\n[bold green]Zero Action Fixer[/bold green] [dim]({provider.model})[/dim]")
    console.print(f"Fixing [dim]{file}[/dim]...\n")

    try:
        raw_response = asyncio.run(stream_fix_response(provider, messages, console))
    except Exception as e:
        logger.bind(category="cli").error(f"Error during streaming fix completion: {e}")
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    fixed_content = _strip_code_fences(raw_response)

    # -- Show diff ------------------------------------------------------------
    _render_diff(original_content, fixed_content, file.name, console)

    if not fixed_content.strip():
        console.print("[bold red]Error:[/bold red] The AI returned an empty response. No changes written.")
        raise typer.Exit(code=1)

    # -- Confirm before writing -----------------------------------------------
    write_target = output if output else file
    console.print(f"\n[bold]Target:[/bold] [white]{write_target.resolve()}[/white]")
    confirm = Confirm.ask("Apply these changes?", default=False)
    if not confirm:
        console.print("[yellow]Fix discarded. No files were modified.[/yellow]")
        raise typer.Exit(code=0)

    # -- Write fixed file -----------------------------------------------------
    try:
        write_target.parent.mkdir(parents=True, exist_ok=True)
        write_target.write_text(fixed_content, encoding="utf-8")
        console.print(
            Panel(
                f"[bold green]✓ Fix Applied![/bold green]\n"
                f"Fixed file written to: [white]{write_target.resolve()}[/white]",
                title="[bold green]Success[/bold green]",
                border_style="green",
                expand=False,
            )
        )
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to write fixed file: {e}")
        console.print(f"[bold red]Error writing fixed file:[/bold red] {e}")
        raise typer.Exit(code=1)
