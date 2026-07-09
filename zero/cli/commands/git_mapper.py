"""CLI subcommand to map Git history, author expertise, and learn patterns from commit logs."""

from pathlib import Path
from typing import Dict, List
import uuid
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError

def run_git_mapper(ctx: typer.Context) -> None:
    """Analyze Git repository history to map developer expertise and learn project patterns."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # Import git lazily to preserve fast CLI startup
    try:
        import git
    except ImportError:
        console.print("[bold red]Error:[/bold red] GitPython is not installed. Please run 'pip install GitPython'.")
        raise typer.Exit(code=1)

    project_path = Path.cwd()
    try:
        repo = git.Repo(project_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        console.print("[bold red]Error:[/bold red] Not a valid Git repository.")
        raise typer.Exit(code=1)

    console.print("[yellow]Analyzing Git repository history...[/yellow]\n")

    # 1. Map authors and counts
    author_commits: Dict[str, int] = {}
    file_authors: Dict[str, Dict[str, int]] = {}
    recent_commits: List[str] = []

    try:
        # Get up to 100 commits
        commits = list(repo.iter_commits(max_count=100))
        for commit in commits:
            author_name = commit.author.name or "Unknown"
            author_commits[author_name] = author_commits.get(author_name, 0) + 1
            
            # Record recent commit messages (first 20)
            if len(recent_commits) < 20:
                # Safely decode commit message
                msg = commit.message
                if isinstance(msg, bytes):
                    msg = msg.decode("utf-8", errors="replace")
                recent_commits.append(f"- {commit.hexsha[:8]} by {author_name}: {msg.strip()}")

            # Check modified files in this commit
            for parent in commit.parents:
                diffs = parent.diff(commit)
                for diff in diffs:
                    file_path = diff.b_path or diff.a_path
                    if file_path:
                        if file_path not in file_authors:
                            file_authors[file_path] = {}
                        file_authors[file_path][author_name] = file_authors[file_path].get(author_name, 0) + 1
    except Exception as e:
        console.print(f"[bold red]Failed to read Git history:[/bold red] {e}")
        raise typer.Exit(code=1)

    if not author_commits:
        console.print("[yellow]No commits found in the repository history.[/yellow]")
        return

    # Print authors table
    author_table = Table(title="[bold green]Developer Contribution Summary (Last 100 Commits)[/bold green]", show_header=True, header_style="bold cyan")
    author_table.add_column("Author", style="bold white")
    author_table.add_column("Commits", justify="right", style="green")

    for author, count in sorted(author_commits.items(), key=lambda x: x[1], reverse=True):
        author_table.add_row(author, str(count))
    console.print(author_table)
    console.print()

    # Get active AI provider to generate summary
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        raise typer.Exit(code=1)

    console.print("[yellow]Analyzing commit patterns with AI...[/yellow]")
    
    commit_history_str = "\n".join(recent_commits)
    system_prompt = (
        "You are an expert software architect. Analyze the provided Git commit history. "
        "Summarize the recent architectural decisions, conventions, and coding patterns used in this project. "
        "Keep the summary clear, highly structured, and concise (under 200 words)."
    )
    user_prompt = f"Here are the recent commits:\n\n{commit_history_str}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        summary_text = provider.chat(messages)
    except Exception as e:
        console.print(f"[bold red]AI Analysis failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Save to memory.db decisions table so it's injected into system prompts
    db_path = config_dir / "memory.db"
    try:
        from zero.storage.sqlite import SQLiteDatabase
        db = SQLiteDatabase(db_path)
        
        decision_id = f"git_{uuid.uuid4().hex[:6]}"
        db.execute(
            "INSERT INTO decisions (id, project_path, title, problem, solution, status) VALUES (?, ?, ?, ?, ?, ?);",
            (
                decision_id,
                str(project_path.resolve()),
                "Git History & Conventions Summary",
                "Understand project conventions from git commit history",
                summary_text,
                "learned"
            )
        )
        
        console.print(Panel(
            f"[bold green]✓ Git history analyzed and saved to memory![/bold green]\n\n"
            f"[white]{summary_text}[/white]\n\n"
            f"[dim]Saved as Learned Rule ID: #{decision_id}[/dim]",
            title="[bold green]AI Git Insights[/bold green]"
        ))
    except Exception as e:
        console.print(f"[bold red]Failed to save insights to database:[/bold red] {e}")
        raise typer.Exit(code=1)
