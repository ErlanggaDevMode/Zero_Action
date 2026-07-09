"""CLI subcommand to automatically parse git logs and generate CHANGELOG updates and release notes."""

import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError

def generate_release_notes(
    ctx: typer.Context,
    version: Optional[str] = typer.Option(None, "--version", "-v", help="The version name for this release (e.g., v1.1.0)"),
) -> None:
    """Analyze git log and generate a professional release notes/changelog update."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    try:
        import git
    except ImportError:
        console.print("[bold red]Error:[/bold red] GitPython is not installed. Run 'pip install GitPython'.")
        raise typer.Exit(code=1)

    project_path = Path.cwd()
    try:
        repo = git.Repo(project_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        console.print("[bold red]Error:[/bold red] Not a valid Git repository.")
        raise typer.Exit(code=1)

    # 1. Identify previous tag or start commit
    latest_tag = None
    sorted_tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime if t.commit else 0)
    if sorted_tags:
        latest_tag = sorted_tags[-1]
        console.print(f"[cyan]Found latest release tag: [bold]{latest_tag.name}[/bold] ({latest_tag.commit.hexsha[:8]})[/cyan]")

    # 2. Extract commit messages since the latest tag or last 50 commits
    commit_messages = []
    try:
        if latest_tag:
            commits = list(repo.iter_commits(f"{latest_tag.commit.hexsha}..HEAD"))
        else:
            commits = list(repo.iter_commits(max_count=50))

        for c in commits:
            msg = c.message
            if isinstance(msg, bytes):
                msg = msg.decode("utf-8", errors="replace")
            commit_messages.append(f"- {c.hexsha[:8]}: {msg.strip().splitlines()[0]}")
    except Exception as e:
        console.print(f"[bold red]Error reading commits:[/bold red] {e}")
        raise typer.Exit(code=1)

    if not commit_messages:
        console.print("[yellow]No new commits found since the last release tag / in history.[/yellow]")
        return

    console.print(f"[cyan]Collected {len(commit_messages)} commit(s) for changelog generation.[/cyan]")

    # 3. Call LLM to format notes
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        raise typer.Exit(code=1)

    console.print("[yellow]Generating release notes and CHANGELOG entry...[/yellow]")
    
    version_title = version or "vNext"
    commits_str = "\n".join(commit_messages)
    
    system_prompt = (
        "You are an elite product release manager. Create a professional markdown CHANGELOG / Release Notes entry "
        "based on the list of commits. Group changes into 'Features', 'Bug Fixes', and 'Internal/Refactoring'. "
        "Ensure the output is clean, has proper list formatting, and is under 250 words."
    )
    user_prompt = f"Release Version: {version_title}\n\nCommits:\n{commits_str}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        notes = provider.chat(messages)
    except Exception as e:
        console.print(f"[bold red]AI Generation failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 4. Save/Append to CHANGELOG.md
    changelog_path = project_path / "CHANGELOG.md"
    new_entry = f"## {version_title}\n\n{notes}\n\n"
    
    try:
        if changelog_path.exists():
            existing_content = changelog_path.read_text(encoding="utf-8")
            changelog_path.write_text(new_entry + existing_content, encoding="utf-8")
            console.print("[green]✓ Prepended new release notes to CHANGELOG.md[/green]")
        else:
            changelog_path.write_text(f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{new_entry}", encoding="utf-8")
            console.print("[green]✓ Created CHANGELOG.md and wrote release notes[/green]")
    except Exception as e:
        console.print(f"[bold red]Failed to write CHANGELOG.md:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(Panel(notes, title=f"[bold green]Release Notes - {version_title}[/bold green]"))
