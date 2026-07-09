"""CLI subcommand to scan repository structure, summarize layout, and cache details."""

from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from zero.services.logging import logger

def format_size(size_bytes: int) -> str:
    """Format size in bytes to a human-readable string."""
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def init(ctx: typer.Context) -> None:
    """Scan the current working directory, display a summary, and cache repository context."""
    from zero.repository.analyzer import analyze_repository
    console = Console()
    cli_context = ctx.obj

    config_dir = cli_context.config_dir
    repo_path = Path.cwd()

    console.print("\n[bold green]Zero Action Repository Intelligence[/bold green]")
    console.print(f"Initializing repository context in [cyan]{repo_path}[/cyan]...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description="Scanning file structure...", total=None)
        
        try:
            summary = analyze_repository(repo_path)
            progress.update(task, description="Repository analysis complete.")
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to scan repository: {e}")
            console.print(f"[bold red]Error:[/bold red] Could not complete repository scan: {e}")
            raise typer.Exit(code=1)

        task_emb = progress.add_task(description="Generating semantic code search embeddings...", total=None)
        try:
            from zero.storage.sqlite import SQLiteDatabase
            from zero.memory.embeddings import RepositoryIndexer
            
            db_path = config_dir / "memory.db"
            db = SQLiteDatabase(db_path)
            
            settings = cli_context.settings
            indexer = RepositoryIndexer(settings, config_dir, repo_path, db)
            
            def update_progress(msg: str) -> None:
                progress.update(task_emb, description=msg)
                
            indexer.index_repository(progress_callback=update_progress)
            progress.update(task_emb, description="Semantic indexing complete.")
        except Exception as e:
            logger.bind(category="cli").warning(f"Failed to index semantic embeddings: {e}")
            progress.update(task_emb, description="[bold yellow]Semantic indexing skipped/failed.[/bold yellow]")

    # 1. Prepare Overview Table
    metrics_table = Table.grid(padding=(0, 2))
    metrics_table.add_column("Key", style="dim cyan")
    metrics_table.add_column("Value", style="bold white")
    metrics_table.add_row("Total Files", str(summary.total_files))
    metrics_table.add_row("Total Size", format_size(summary.total_size_bytes))
    metrics_table.add_row("Docker config", "Yes" if (summary.has_docker or summary.has_docker_compose) else "No")

    # 2. Languages Table
    lang_table = Table(show_header=True, header_style="bold magenta", box=None)
    lang_table.add_column("Language")
    lang_table.add_column("Files", justify="right")
    for lang, count in sorted(summary.languages.items(), key=lambda x: x[1], reverse=True):
        lang_table.add_row(lang, str(count))

    # 3. Frameworks list
    frameworks_text = ", ".join(summary.frameworks) if summary.frameworks else "None detected"
    
    # 4. Git block
    git_table = Table.grid(padding=(0, 2))
    git_table.add_column("Key", style="dim green")
    git_table.add_column("Value", style="bold white")
    if summary.git_branch:
        git_table.add_row("Branch", summary.git_branch)
        git_table.add_row("Commit Hash", summary.git_commit_hash[:8] if summary.git_commit_hash else "N/A")
        git_table.add_row("Commit Msg", summary.git_commit_message or "N/A")
        status_str = "[bold red]Dirty[/bold red]" if summary.git_is_dirty else "[green]Clean[/green]"
        git_table.add_row("Status", status_str)
    else:
        git_table.add_row("Git", "Not initialized")

    # Layout rendering
    col_table = Table.grid(padding=(0, 4))
    col_table.add_column()
    col_table.add_column()
    
    lang_panel = Panel(lang_table, title="Languages", border_style="magenta", expand=False)
    git_panel = Panel(git_table, title="Git Status", border_style="green", expand=False)
    
    col_table.add_row(lang_panel, git_panel)

    console.print(
        Panel(
            metrics_table,
            title="Overview Metrics",
            border_style="cyan",
            expand=False
        )
    )
    
    if summary.languages or summary.git_branch:
        console.print(col_table)
        
    if summary.frameworks:
        console.print(Panel(Text(frameworks_text, style="bold yellow"), title="Detected Frameworks", border_style="yellow", expand=False))

    # Write Cache
    cache_dir = config_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "repo_summary.json"
    
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))
        console.print(f"\n[green]✓[/green] Repository summary cached to [dim]{cache_path}[/dim]\n")
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to cache repository summary: {e}")
        console.print(f"[bold yellow]Warning:[/bold yellow] Could not cache repository summary: {e}")
