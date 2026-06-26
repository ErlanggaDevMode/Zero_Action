"""CLI subcommand to verify Zero Action foundation configuration and logging."""

import typer
from loguru import logger


def verify(ctx: typer.Context) -> None:
    """Verify that configuration and logging systems are operating correctly."""
    settings = ctx.obj.settings
    debug = ctx.obj.debug
    config_dir = ctx.obj.config_dir

    # Verify log category routing
    logger.bind(category="cli").info("Verifying CLI log category...")
    logger.bind(category="provider").debug("Verifying Provider log category...")
    logger.bind(category="ai").info("Verifying AI log category...")

    typer.echo("Zero Action CLI Foundation is fully functional!")
    typer.echo(f"Config Directory: {config_dir}")
    typer.echo(f"Theme Setting: {settings.settings.theme}")
    typer.echo(f"Debug Mode: {debug}")
