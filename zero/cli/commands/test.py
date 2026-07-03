"""CLI subcommand to execute test runners or linters with autonomous AI self-healing capabilities."""

import asyncio
import difflib
import re
import subprocess
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from zero.services.logging import logger

app = typer.Typer()

def _strip_code_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences if the AI accidentally includes them."""
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)

def _render_diff(original: str, fixed: str, filename: str, console: Console) -> None:
    """Render a unified diff between original and fixed content."""
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
            title="[bold cyan]Proposed Self-Healing Fix (Diff)[/bold cyan]",
            border_style="cyan",
            expand=True,
        )
    )

def _detect_failing_file(output_text: str) -> Optional[Path]:
    """Parse traceback or linter outputs to detect a local file that failed."""
    # Pattern 1: Python traceback (File "path/to/file.py", line 12)
    matches_tb = re.findall(r'File "([^"]+)", line \d+', output_text)
    
    # Pattern 2: Standard linter/compiler (path/to/file.py:12:34 or path/to/file.py:12:)
    matches_lint = re.findall(r'([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9_]+):\d+:', output_text)
    
    # Combine matches
    all_matches = matches_tb + matches_lint
    
    for match in all_matches:
        try:
            p = Path(match.strip())
            # Ensure file exists, is a file, and is relative to current working directory
            if p.exists() and p.is_file():
                # Check it is in the repository
                cwd_resolved = Path.cwd().resolve()
                p_resolved = p.resolve()
                if p_resolved.is_relative_to(cwd_resolved):
                    return p
        except Exception:
            continue
    return None

def test(
    ctx: typer.Context,
    command: str = typer.Option("pytest", "--command", "-c", help="The test runner or linter command to run"),
    max_iterations: int = typer.Option(3, "--max-iterations", "-m", help="Maximum self-healing attempts"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Target source file to apply fixes on (auto-detects if omitted)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve AI changes without prompting"),
    pipeline: bool = typer.Option(False, "--pipeline", "-p", help="Run the multi-stage quality pipeline (ruff check && mypy zero tests && pytest)"),
) -> None:
    """Run tests or linters and recursively self-heal code errors using AI."""
    from zero.services.ai import AIService
    from zero.core.exceptions import ConfigError
    
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
    if pipeline and command == "pytest":
        command = "ruff check && mypy zero tests && pytest"

    console.print(f"\n[bold green]Zero Action Self-Healing Runner[/bold green] [dim]({provider.model})[/dim]")
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        console.print(f"\n[bold yellow]--- Iteration {iteration}/{max_iterations} ---[/bold yellow]")
        console.print(f"Running command: [bold cyan]{command}[/bold cyan]...")
        
        # Execute the check command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        # Print output to terminal
        if result.stdout:
            console.print(result.stdout)
        if result.stderr:
            console.print(result.stderr, style="dim red")
            
        if result.returncode == 0:
            console.print(f"\n[bold green]✓ Command succeeded! All checks passed on iteration {iteration}.[/bold green]\n")
            raise typer.Exit(code=0)
            
        console.print(f"\n[bold red]✗ Command failed with exit code {result.returncode}[/bold red]")
        
        # Determine file to fix
        target_file = file
        if not target_file:
            combined_output = (result.stdout or "") + "\n" + (result.stderr or "")
            target_file = _detect_failing_file(combined_output)
            
        if not target_file:
            console.print("[bold yellow]Could not auto-detect any failing source files from command output.[/bold yellow]")
            if not yes:
                try:
                    file_input = typer.prompt("Please specify the file path to fix (or press Enter to abort)", default="", show_default=False)
                    if not file_input.strip():
                        console.print("[yellow]Self-healing aborted.[/yellow]")
                        raise typer.Exit(code=1)
                    target_file = Path(file_input)
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[yellow]Self-healing aborted.[/yellow]")
                    raise typer.Exit(code=1)
            else:
                console.print("[bold red]Self-healing failed: No file detected and running in auto-approve mode.[/bold red]")
                raise typer.Exit(code=1)

        if not target_file.exists() or not target_file.is_file():
            console.print(f"[bold red]Error:[/bold red] Target file '{target_file}' does not exist or is not a file.")
            raise typer.Exit(code=1)

        console.print(f"Targeting file for self-healing: [bold cyan]{target_file}[/bold cyan]")
        
        # Load file content
        try:
            original_content = target_file.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error reading file {target_file}:[/bold red] {e}")
            raise typer.Exit(code=1)

        # Build prompt instructions
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

        system_context = ai_service.get_system_prompt(Path.cwd())
        system_prompt = f"{system_context}\n\n{fixer_instructions}"
        
        combined_error = f"Command executed: {command}\nExit Code: {result.returncode}\n\nOutput Log:\n"
        if result.stdout:
            combined_error += f"--- stdout ---\n{result.stdout}\n"
        if result.stderr:
            combined_error += f"--- stderr ---\n{result.stderr}\n"

        user_prompt = (
            f"Fix the following source file to resolve the command execution failure.\n\n"
            f"**File:** {target_file}\n\n"
            f"**Current Content:**\n```\n{original_content}\n```\n\n"
            f"**Execution Log Error:**\n```\n{combined_error}\n```"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        console.print("\n[yellow]Querying AI for self-healing fix...[/yellow]")
        try:
            from zero.core.ui import stream_completion_with_timer
            raw_response = asyncio.run(stream_completion_with_timer(provider, messages, console))
        except Exception as e:
            console.print(f"\n[bold red]API Completion Error during self-healing:[/bold red] {e}")
            raise typer.Exit(code=1)

        fixed_content = _strip_code_fences(raw_response)
        
        # Show diff
        _render_diff(original_content, fixed_content, target_file.name, console)

        if not fixed_content.strip():
            console.print("[bold red]Self-healing failed: AI returned empty response.[/bold red]")
            raise typer.Exit(code=1)

        # Confirm
        if not yes:
            try:
                confirm = Confirm.ask("Apply this self-healing fix?", default=False)
                if not confirm:
                    console.print("[yellow]Fix discarded. Self-healing aborted.[/yellow]")
                    raise typer.Exit(code=0)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Self-healing aborted.[/yellow]")
                raise typer.Exit(code=1)

        # Write fixed code
        try:
            target_file.write_text(fixed_content, encoding="utf-8")
            console.print("[green]✓ Suggested fix applied. Re-running checks...[/green]")
        except Exception as e:
            console.print(f"[bold red]Failed to write fix to {target_file}:[/bold red] {e}")
            raise typer.Exit(code=1)

    console.print(f"\n[bold red]✗ Self-healing reached maximum iterations ({max_iterations}) but the command is still failing.[/bold red]\n")
    raise typer.Exit(code=1)
