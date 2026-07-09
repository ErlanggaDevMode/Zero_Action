"""CLI subcommand to automatically generate unit tests for Python modules with self-healing checks."""

import asyncio
import difflib
import subprocess
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError
from zero.core.ui import stream_completion_with_timer
from zero.cli.commands.test import _strip_code_fences

def _render_diff(original: str, fixed: str, filename: str, console: Console) -> None:
    """Render a unified diff between original and generated test content."""
    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"original/{filename}",
            tofile=f"generated/{filename}",
            lineterm="",
        )
    )
    if not diff_lines:
        console.print("[yellow]No differences or new test code generated.[/yellow]")
        return

    diff_text = "".join(diff_lines)
    console.print(
        Panel(
            Syntax(diff_text, "diff", theme="monokai", line_numbers=False),
            title="[bold cyan]Proposed Test Modifications (Diff)[/bold cyan]",
            border_style="cyan",
            expand=True,
        )
    )

def run_test_gen(
    ctx: typer.Context,
    file: Path = typer.Argument(..., help="Target source file to generate unit tests for"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Custom output test file path"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve and write generated test file without prompting"),
    max_fix_attempts: int = typer.Option(2, "--attempts", "-a", help="Maximum test self-healing attempts if quality checks fail"),
) -> None:
    """Automatically analyze a file and generate robust unit tests with pytest."""
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

    target_file = Path(file).resolve()
    if not target_file.exists() or not target_file.is_file():
        console.print(f"[bold red]Error:[/bold red] Target file does not exist or is not a file: {target_file}")
        raise typer.Exit(code=1)

    # Determine default output test file path if not provided
    if not output:
        tests_dir = Path.cwd() / "tests"
        if not tests_dir.exists():
            tests_dir.mkdir(exist_ok=True)

        try:
            rel_path = target_file.relative_to(Path.cwd())
            parts = list(rel_path.parts)
            # Strip parent dir (e.g. 'zero' or 'src') if there's any hierarchy
            if len(parts) > 1:
                parts = parts[1:]
            
            parts[-1] = f"test_{parts[-1]}"
            
            if (tests_dir / "unit").exists():
                output_file = (tests_dir / "unit" / Path(*parts)).resolve()
            else:
                output_file = (tests_dir / Path(*parts)).resolve()
        except Exception:
            output_file = (tests_dir / f"test_{target_file.name}").resolve()
    else:
        output_file = Path(output).resolve()

    console.print(f"\n[bold green]Zero Action Unit Test Generator[/bold green] [dim]({provider.model})[/dim]")
    console.print(f"Target File: [cyan]{target_file}[/cyan]")
    console.print(f"Destination: [cyan]{output_file}[/cyan]\n")

    try:
        file_content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[bold red]Error reading target file:[/bold red] {e}")
        raise typer.Exit(code=1)

    system_context = ai_service.get_system_prompt(Path.cwd())
    system_prompt = (
        f"{system_context}\n\n"
        "You are a Senior QA/Python developer specializing in test suites. "
        "Generate complete, clean, and robust unit tests using 'pytest'. "
        "Appropriately mock all external calls (APIs, networks, file IO, or subprocess commands) using unittest.mock. "
        "Write tests that cover basic execution paths, success scenarios, and common failure/exception paths. "
        "Do NOT write empty placeholders. Return ONLY the complete valid Python code inside triple backticks (```python ... ```)."
    )

    user_prompt = (
        f"Generate a robust unit test suite for the file '{target_file.name}'.\n\n"
        f"**File Content:**\n```python\n{file_content}\n```"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    console.print("[yellow]Analyzing target file and generating tests...[/yellow]")
    try:
        raw_response = asyncio.run(stream_completion_with_timer(provider, messages, console))
    except Exception as e:
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    generated_tests = _strip_code_fences(raw_response)
    if not generated_tests.strip():
        console.print("[bold red]AI returned empty response. Test generation failed.[/bold red]")
        raise typer.Exit(code=1)

    # Show preview or diff if file exists
    original_test_content = ""
    if output_file.exists():
        try:
            original_test_content = output_file.read_text(encoding="utf-8")
            _render_diff(original_test_content, generated_tests, output_file.name, console)
        except Exception:
            pass
    else:
        console.print("\n[bold cyan]Preview of Generated Unit Tests:[/bold cyan]")
        console.print(Syntax(generated_tests, "python", theme="monokai", line_numbers=True))

    # Confirm before writing
    if not yes:
        try:
            confirm = Confirm.ask(f"Write generated tests to {output_file.name}?", default=False)
            if not confirm:
                console.print("[yellow]Test generation discarded.[/yellow]")
                raise typer.Exit(code=0)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Test generation aborted.[/yellow]")
            raise typer.Exit(code=1)

    # Write output test file
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(generated_tests, encoding="utf-8")
        console.print(f"[green]✓ Successfully wrote tests to {output_file}[/green]")
    except Exception as e:
        console.print(f"[bold red]Failed to write generated test file:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Run self-healing validation loop on the generated test file
    attempt = 0
    success = False
    
    while attempt < max_fix_attempts and not success:
        attempt += 1
        console.print(f"\n[yellow]Validating tests (Attempt {attempt}/{max_fix_attempts})...[/yellow]")
        console.print(f"Executing: [bold cyan]ruff check {output_file.name} && pytest {output_file.name}[/bold cyan]")
        
        # Use relative paths for executing checks to avoid issues
        rel_output = output_file.name
        try:
            rel_output = str(output_file.relative_to(Path.cwd()))
        except Exception:
            pass

        # Check with ruff linter
        ruff_res = subprocess.run(["uv", "run", "ruff", "check", rel_output], capture_output=True, text=True)
        # Check with pytest
        pytest_res = subprocess.run(["uv", "run", "pytest", rel_output], capture_output=True, text=True)

        if ruff_res.returncode == 0 and pytest_res.returncode == 0:
            console.print("[bold green]✓ Generated unit tests passed all syntax and assertion checks successfully![/bold green]")
            success = True
        else:
            console.print("[bold red]✗ Quality checks failed for the generated unit tests.[/bold red]")
            combined_error = ""
            if ruff_res.returncode != 0:
                console.print(f"[dim red]Ruff Output:\n{ruff_res.stdout or ruff_res.stderr}[/dim red]")
                combined_error += f"--- Ruff linter error ---\n{ruff_res.stdout or ruff_res.stderr}\n"
            if pytest_res.returncode != 0:
                console.print(f"[dim red]Pytest Output:\n{pytest_res.stdout or pytest_res.stderr}[/dim red]")
                combined_error += f"--- Pytest execution error ---\n{pytest_res.stdout or pytest_res.stderr}\n"

            if attempt >= max_fix_attempts:
                break

            console.print("[yellow]Querying AI self-healing to fix generated unit tests...[/yellow]")
            fix_prompt = (
                f"The generated unit test file failed checks. Fix all syntax, linter, or assertion issues in the test file.\n\n"
                f"**Target Code Content:**\n```python\n{file_content}\n```\n\n"
                f"**Generated Test Content:**\n```python\n{generated_tests}\n```\n\n"
                f"**Error logs:**\n```\n{combined_error}\n```\n\n"
                f"Return ONLY the complete corrected Python test code inside triple backticks (```python ... ```)."
            )
            try:
                raw_fix = provider.chat([{"role": "user", "content": fix_prompt}])
                generated_tests = _strip_code_fences(raw_fix)
                if generated_tests.strip():
                    output_file.write_text(generated_tests, encoding="utf-8")
                    console.print("[green]Self-healing fix applied. Re-running checks...[/green]")
                else:
                    console.print("[bold red]Self-healing failed: AI returned empty fix response.[/bold red]")
                    break
            except Exception as e:
                console.print(f"[bold red]Self-healing query failed:[/bold red] {e}")
                break

    if not success:
        console.print("[bold yellow]⚠️  Test file written but continues to fail checks. Manual resolution may be required.[/bold yellow]")
