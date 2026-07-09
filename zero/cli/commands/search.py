"""CLI subcommands to perform web searches and read webpage content directly in the terminal."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()

def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="The search query to look up on the web"),
) -> None:
    """Perform a web search using DuckDuckGo HTML and display formatted results."""
    from zero.services.search import search_ddg
    
    console = Console()
    console.print(f"\n[bold yellow]Searching the web for:[/bold yellow] [cyan]{query}[/cyan]...\n")
    
    results = search_ddg(query)
    
    if not results or (len(results) == 1 and results[0]["title"] == "Error"):
        err_msg = results[0]["snippet"] if results else "No results found."
        console.print(f"[bold red]Search Failed:[/bold red] {err_msg}")
        raise typer.Exit(code=1)

    table = Table(title=f"Web Search Results for '{query}'", border_style="yellow")
    table.add_column("Index", justify="center", style="dim", width=6)
    table.add_column("Title & URL", style="bold cyan")
    table.add_column("Snippet", style="white")

    for i, res in enumerate(results, 1):
        title_url = f"[bold]{res['title']}[/bold]\n[dim]{res['url']}[/dim]"
        table.add_row(str(i), title_url, res["snippet"])

    console.print(table)
    console.print()

def read(
    ctx: typer.Context,
    url: str = typer.Argument(..., help="The webpage HTTP URL to read and parse"),
) -> None:
    """Fetch webpage HTML, strip styling and tags, and print the readable text context."""
    from zero.services.search import fetch_url_text
    
    console = Console()
    console.print(f"\n[bold yellow]Reading URL contents:[/bold yellow] [cyan]{url}[/cyan]...\n")
    
    text = fetch_url_text(url)
    
    if text.startswith("Error reading URL"):
        console.print(f"[bold red]{text}[/bold red]\n")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            text,
            title=f"[bold green]Webpage Context: {url}[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()
