"""CLI subcommand to update Zero Action CLI to the latest version."""

import subprocess
import sys
from pathlib import Path
from rich.console import Console

console = Console()


def update() -> None:
    """Update Zero Action CLI to the latest version from git and rebuild dependencies."""
    console.print("[bold cyan]🔄 Starting Zero Action Auto-Update...[/bold cyan]\n")

    # Determine if we should use shell execution (required on Windows for local PATH resolution)
    use_shell = (sys.platform == "win32")

    # 1. Try Git Pull
    git_dir = Path(__file__).resolve().parents[3] / ".git"
    if git_dir.exists():
        console.print("[yellow]Git repository detected. Pulling latest changes...[/yellow]")
        try:
            # Get current branch
            branch_res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                shell=use_shell
            )
            branch = branch_res.stdout.strip() or "main"
            
            # Git pull
            pull_res = subprocess.run(
                ["git", "pull", "origin", branch],
                capture_output=True,
                text=True,
                check=True,
                shell=use_shell
            )
            console.print(f"[green]✓ Successfully pulled changes from branch '{branch}':[/green]")
            console.print(f"[dim]{pull_res.stdout}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Error running git pull:[/bold red] {e}")
            console.print("[yellow]Continuing with tool re-installation...[/yellow]\n")
    else:
        console.print("[dim]Not in a git repository. Skipping git pull...[/dim]")

    # 2. Re-install/re-sync global tool
    console.print("[yellow]Syncing and updating package installations...[/yellow]")
    
    package_root = Path(__file__).resolve().parents[3]
    
    # Run uv tool installation update
    try:
        console.print("[dim]Running: uv tool install --force --editable .[/dim]")
        install_res = subprocess.run(
            ["uv", "tool", "install", "--force", "--editable", "."],
            cwd=str(package_root),
            capture_output=True,
            text=True,
            shell=use_shell
        )
        if install_res.returncode == 0:
            console.print("[green]✓ Successfully reinstalled Zero Action global tool using uv![/green]")
            console.print(f"[dim]{install_res.stdout}[/dim]")
            console.print("\n🎉 [bold green]Zero Action CLI is up-to-date![/bold green]")
            return
        else:
            console.print(f"[yellow]uv tool update failed with exit code {install_res.returncode}: {install_res.stderr.strip()}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]uv command not found or failed to start: {e}[/yellow]")

    # Fallback to pip install if uv is not available/failed (calling global pip directly)
    try:
        console.print("[dim]Running: pip install -e .[/dim]")
        install_res = subprocess.run(
            ["pip", "install", "-e", "."],
            cwd=str(package_root),
            capture_output=True,
            text=True,
            shell=use_shell
        )
        if install_res.returncode == 0:
            console.print("[green]✓ Successfully reinstalled Zero Action global tool using pip![/green]")
            console.print("\n🎉 [bold green]Zero Action CLI is up-to-date![/bold green]")
            return
        else:
            console.print(f"[bold red]Reinstallation failed:[/bold red] {install_res.stderr.strip()}")
    except Exception as e:
        console.print(f"[bold red]Could not reinstall package dependencies: {e}[/bold red]")

    console.print("\n[bold yellow]⚠️ Update completed with warnings. Please verify command execution manually.[/bold yellow]")
