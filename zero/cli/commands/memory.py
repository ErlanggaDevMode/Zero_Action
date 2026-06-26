"""CLI commands for managing conversation memory, ADRs, and knowledge import."""

import uuid
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from zero.memory.manager import MemoryManager
from zero.services.logging import logger

memory_app = typer.Typer(
    name="memory",
    help="[bold green]Zero Action Memory[/bold green]: Manage active chats, decisions, and knowledge base.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

def get_memory_manager(ctx: typer.Context) -> MemoryManager:
    """Helper to initialize and return MemoryManager from context config directory."""
    cli_context = ctx.obj
    config_dir = cli_context.config_dir
    db_path = config_dir / "memory.db"
    return MemoryManager(db_path)

@memory_app.command("list-sessions")
def list_sessions(ctx: typer.Context) -> None:
    """List all saved chat sessions."""
    console = Console()
    manager = get_memory_manager(ctx)
    sessions = manager.sessions.list_sessions()
    
    if not sessions:
        console.print("[yellow]No saved chat sessions found.[/yellow]")
        return
        
    table = Table(title="[bold green]Saved Chat Sessions[/bold green]", show_header=True, header_style="bold cyan")
    table.add_column("Session ID", style="dim")
    table.add_column("Title", style="bold white")
    table.add_column("Last Active", style="magenta")
    
    for sess in sessions:
        table.add_row(sess["id"], sess["title"], sess["updated_at"])
        
    console.print(table)

@memory_app.command("show-session")
def show_session(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The ID of the session to display")
) -> None:
    """Display the conversation history for a specific chat session."""
    console = Console()
    manager = get_memory_manager(ctx)
    session = manager.sessions.get_session(session_id)
    
    if not session:
        console.print(f"[bold red]Error:[/bold red] Chat session '{session_id}' not found.")
        raise typer.Exit(code=1)
        
    messages = manager.sessions.get_messages(session_id)
    console.print(Panel(f"[bold white]Title:[/bold white] {session['title']}\n[bold white]ID:[/bold white] {session_id}", title="Session Details", border_style="cyan"))
    
    if not messages:
        console.print("[dim]No messages in this conversation session.[/dim]")
        return
        
    for msg in messages:
        role = msg["role"].upper()
        role_style = "bold yellow" if role == "USER" else "bold green"
        content = msg["content"]
        console.print(f"\n[{role_style}]{role}:[/{role_style}]")
        console.print(content)
    console.print()

@memory_app.command("delete-session")
def delete_session(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The ID of the session to delete")
) -> None:
    """Delete a chat session and all its messages."""
    console = Console()
    manager = get_memory_manager(ctx)
    session = manager.sessions.get_session(session_id)
    
    if not session:
        console.print(f"[bold red]Error:[/bold red] Chat session '{session_id}' not found.")
        raise typer.Exit(code=1)
        
    manager.sessions.delete_session(session_id)
    console.print(f"[green]✓[/green] Successfully deleted chat session '{session_id}' and all associated messages.")

@memory_app.command("add-decision")
def add_decision(
    ctx: typer.Context,
    title: str = typer.Option(None, "--title", "-t", help="Title of the decision"),
    problem: str = typer.Option(None, "--problem", "-p", help="Problem statement"),
    solution: str = typer.Option(None, "--solution", "-s", help="Proposed/implemented solution"),
    status: str = typer.Option("accepted", "--status", help="Decision status (e.g. accepted, proposed, deprecated)")
) -> None:
    """Interactively or via options record an architectural decision (ADR)."""
    console = Console()
    manager = get_memory_manager(ctx)
    project_path = str(Path.cwd().resolve())
    
    if not title:
        title = typer.prompt("Decision Title")
    if not problem:
        problem = typer.prompt("Problem/Context")
    if not solution:
        solution = typer.prompt("Chosen Solution")
        
    decision_id = str(uuid.uuid4())[:8]
    try:
        manager.decisions.add_decision(
            decision_id=decision_id,
            project_path=project_path,
            title=title,
            problem=problem,
            solution=solution,
            status=status
        )
        console.print(f"[green]✓[/green] Recorded Technical Decision [bold cyan]#{decision_id}[/bold cyan] for workspace '{project_path}'.")
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to record decision: {e}")
        console.print(f"[bold red]Error:[/bold red] Failed to record decision: {e}")
        raise typer.Exit(code=1)

@memory_app.command("list-decisions")
def list_decisions(ctx: typer.Context) -> None:
    """List all technical decisions logged in this workspace."""
    console = Console()
    manager = get_memory_manager(ctx)
    project_path = str(Path.cwd().resolve())
    decisions = manager.decisions.list_decisions(project_path)
    
    if not decisions:
        console.print("[yellow]No logged technical decisions found for this workspace.[/yellow]")
        return
        
    table = Table(title="[bold green]Technical Decisions Log[/bold green]", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold white")
    table.add_column("Status", style="magenta")
    table.add_column("Date", style="blue")
    
    for dec in decisions:
        status = dec["status"].lower()
        status_color = "green" if status == "accepted" else "yellow" if status == "proposed" else "red"
        status_str = f"[{status_color}]{status}[/{status_color}]"
        
        table.add_row(dec["id"], dec["title"], status_str, dec["created_at"])
        
    console.print(table)

@memory_app.command("import-knowledge")
def import_knowledge(
    ctx: typer.Context,
    file_path: Path = typer.Argument(..., help="Path to text or markdown file to import")
) -> None:
    """Import reference files or wikis into the knowledge base."""
    console = Console()
    manager = get_memory_manager(ctx)
    
    if not file_path.exists():
        console.print(f"[bold red]Error:[/bold red] Reference file '{file_path}' does not exist.")
        raise typer.Exit(code=1)
        
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        title = file_path.name
        source = str(file_path.resolve())
        knowledge_id = str(uuid.uuid4())[:8]
        
        manager.knowledge.add_knowledge(
            knowledge_id=knowledge_id,
            title=title,
            content=content,
            source=source
        )
        console.print(f"[green]✓[/green] Knowledge base successfully imported file [bold cyan]'{title}'[/bold cyan] (ID: #{knowledge_id}).")
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to import file: {e}")
        console.print(f"[bold red]Error:[/bold red] Failed to import knowledge: {e}")
        raise typer.Exit(code=1)
