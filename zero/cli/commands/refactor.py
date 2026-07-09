import typer
import subprocess
from pathlib import Path
from rich.console import Console
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError

def refactor(
    ctx: typer.Context,
    file: Path = typer.Option(..., "--file", "-f", help="Target file to refactor"),
    instruction: str = typer.Option(..., "--instruction", "-i", help="Refactoring instruction"),
    max_attempts: int = typer.Option(2, "--attempts", "-a", help="Maximum refactor fix attempts if tests fail"),
) -> None:
    """Agentic Refactor Wizard: apply AI edits, test, and auto-rollback on failure."""
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
        
    cwd = Path.cwd().resolve()
    from git import Repo
    repo = Repo(cwd)
    
    target_file = Path(file).resolve()
    if not target_file.exists():
        console.print(f"[bold red]Error:[/bold red] Target file does not exist: {target_file}")
        raise typer.Exit(code=1)
        
    original_content = target_file.read_text(encoding="utf-8")
    
    console.print(f"\n[bold green]Zero Action Refactor Wizard[/bold green] [dim]({provider.model})[/dim]")
    try:
        rel_path = str(target_file.relative_to(cwd))
    except Exception:
        rel_path = target_file.name
    console.print(f"Refactoring target: [dim]{rel_path}[/dim]")
    console.print(f"Instruction: [cyan]{instruction}[/cyan]\n")
    
    prompt = (
        f"You are a refactoring engine. Refactor the file '{target_file.name}' according to this instruction:\n"
        f"\"{instruction}\"\n\n"
        f"Here is the original file content:\n"
        f"```\n{original_content}\n```\n\n"
        f"Return ONLY the complete refactored file content enclosed in standard code blocks (```python ... ```)."
    )
    
    attempt = 0
    success = False
    
    while attempt < max_attempts and not success:
        attempt += 1
        console.print(f"[yellow]Attempt {attempt}/{max_attempts}: Querying AI for refactoring...[/yellow]")
        
        try:
            raw_response = provider.chat([{"role": "user", "content": prompt}])
            from zero.cli.commands.fix import _strip_code_fences
            fixed_content = _strip_code_fences(raw_response)
            
            if not fixed_content.strip():
                console.print("[bold red]AI returned empty response. Retrying...[/bold red]")
                continue
                
            target_file.write_text(fixed_content, encoding="utf-8")
            console.print("[green]Refactored content written to file. Running quality checks...[/green]")
            
            # Run pipeline checks: ruff and pytest
            console.print("Executing: [bold cyan]ruff check && pytest[/bold cyan]")
            ruff_res = subprocess.run(["uv", "run", "ruff", "check", str(target_file)], capture_output=True, text=True)
            pytest_res = subprocess.run(["uv", "run", "pytest"], capture_output=True, text=True)
            
            if ruff_res.returncode == 0 and pytest_res.returncode == 0:
                console.print("[bold green]✓ Refactoring successfully passed all quality checks![/bold green]")
                success = True
            else:
                console.print("[bold red]✗ Refactoring failed quality checks.[/bold red]")
                if ruff_res.returncode != 0:
                    console.print(f"[dim red]Ruff Output:\n{ruff_res.stdout or ruff_res.stderr}[/dim red]")
                if pytest_res.returncode != 0:
                    console.print(f"[dim red]Pytest Output:\n{pytest_res.stdout or pytest_res.stderr}[/dim red]")
                
                console.print("[yellow]Autonomously rolling back changes...[/yellow]")
                repo.git.checkout(str(target_file))
                
                prompt = (
                    f"Your previous refactoring attempt failed checks. Refactor the file '{target_file.name}' according to this instruction:\n"
                    f"\"{instruction}\"\n\n"
                    f"Ruff failure log: {ruff_res.stdout or ruff_res.stderr}\n"
                    f"Pytest failure log: {pytest_res.stdout or pytest_res.stderr}\n\n"
                    f"Here is the original file content:\n"
                    f"```\n{original_content}\n```\n\n"
                    f"Provide a corrected complete refactored file content inside code fences."
                )
        except Exception as e:
            console.print(f"[bold red]Refactoring attempt error:[/bold red] {e}")
            repo.git.checkout(str(target_file))
            
    if not success:
        console.print("[bold red]✗ Refactor Wizard was unable to successfully refactor without failing checks. Original code restored.[/bold red]")
        raise typer.Exit(code=1)
