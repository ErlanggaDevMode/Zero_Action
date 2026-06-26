"""CLI subcommand to display application version and runtime environment details."""

import platform
import sys
import typer
from rich.console import Console
from rich.table import Table
from zero.version import __version__


def version(ctx: typer.Context) -> None:
    """Display Zero Action CLI version and environment details."""
    cli_context = ctx.obj
    config_dir = cli_context.config_dir

    console = Console()

    table = Table(
        title="[bold green]Zero Action CLI System Environment[/bold green]",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Property", style="dim")
    table.add_column("Value", style="bold white")

    table.add_row("CLI Version", __version__)
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Platform", f"{platform.system()} ({platform.release()})")
    table.add_row("Config Directory", str(config_dir))

    console.print(table)
