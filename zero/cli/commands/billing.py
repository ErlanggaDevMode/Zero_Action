import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from zero.services.billing import get_billing_summary

def billing(ctx: typer.Context) -> None:
    """Display the summarized token usage and estimated API cost dashboard."""
    console = Console()
    summary = get_billing_summary()
    
    table = Table(
        title="[bold green]Zero Action Billing & API Usage Dashboard[/bold green]",
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Completion Calls", str(summary["total_calls"]))
    table.add_row("Total Prompt Tokens", f"{summary['total_prompt_tokens']:,}")
    table.add_row("Total Completion Tokens", f"{summary['total_completion_tokens']:,}")
    table.add_row("Total Tokens Consumed", f"{summary['total_prompt_tokens'] + summary['total_completion_tokens']:,}")
    table.add_row("Total Estimated Cost", f"${summary['total_cost']:.6f} USD")
    
    console.print(Panel(table, border_style="green", expand=False))
