"""Main Typer application setup and callbacks for CLI Layer."""

import os
from pathlib import Path
from typing import Optional
import typer
from loguru import logger
from zero.cli.context import CliContext
from zero.core.exceptions import ZeroError
from zero.services.config import load_config
from zero.services.logging import setup_logging
from zero.cli.commands.verify import verify
from zero.cli.commands.version import version
from zero.cli.commands.config import config_app
from zero.cli.commands.setup import setup
from zero.cli.commands.init import init
from zero.cli.commands.memory import memory_app
from zero.cli.commands.ask import ask
from zero.cli.commands.chat import chat

app = typer.Typer(
    name="zero",
    help="[bold green]Zero Action[/bold green]: AI Development Partner CLI",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    debug: Optional[bool] = typer.Option(
        None, "--debug", "-d", help="Enable debug logging output."
    ),
    verbose: Optional[bool] = typer.Option(
        None, "--verbose", "-v", help="Enable verbose console output."
    ),
) -> None:
    """Initialize CLI configurations and logging."""
    try:
        env_home = os.environ.get("ZERO_HOME")
        config_dir = Path(env_home) if env_home else Path.home() / ".zero"
        settings = load_config(config_dir)

        # CLI flag takes precedence over config file
        is_debug = debug if debug is not None else settings.app.debug

        # Setup logging under ~/.zero/logs
        setup_logging(config_dir / "logs", debug_mode=is_debug)

        # Use type-safe CliContext
        ctx.obj = CliContext(
            settings=settings,
            debug=is_debug,
            config_dir=config_dir,
        )

        logger.bind(category="cli").debug("Zero Action CLI foundation successfully initialized.")

    except ZeroError as e:
        typer.echo(f"Initialization Error: {e.message}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Unexpected Initialization Error: {e}", err=True)
        raise typer.Exit(code=1)


# Register subcommands from commands package
app.command("verify")(verify)
app.command("version")(version)
app.command("setup")(setup)
app.command("init")(init)
app.command("ask")(ask)
app.command("chat")(chat)
app.add_typer(config_app)
app.add_typer(memory_app)
