"""CLI subcommands to display and edit Zero Action configurations."""

from typing import Any
import typer
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.tree import Tree
from zero.services.config import save_config, ZeroSettings

config_app = typer.Typer(
    name="config",
    help="Manage Zero Action configurations.",
    no_args_is_help=True,
)


@config_app.command("show")
def show(ctx: typer.Context) -> None:
    """Show the current configuration tree, masking sensitive values."""
    settings = ctx.obj.settings
    console = Console()

    tree = Tree("[bold green]Zero Action Configurations[/bold green]")

    # App section
    app_tree = tree.add("[cyan]App Settings[/cyan]")
    app_tree.add(f"debug: [white]{settings.app.debug}[/white]")
    app_tree.add(f"verbose: [white]{settings.app.verbose}[/white]")

    # Settings section
    settings_tree = tree.add("[cyan]Global Settings[/cyan]")
    settings_tree.add(f"theme: [white]{settings.settings.theme}[/white]")

    # Provider section
    provider_tree = tree.add("[cyan]Provider Settings[/cyan]")
    provider_tree.add(f"active_provider: [yellow]'{settings.provider.active_provider}'[/yellow]")

    providers = settings.provider
    for prov_name in [
        "openai",
        "anthropic",
        "gemini",
        "openrouter",
        "ollama",
        "groq",
        "azure",
        "deepseek",
        "mistral",
        "compatible",
    ]:
        prov_settings = getattr(providers, prov_name)
        prov_sub = provider_tree.add(f"[magenta]{prov_name}[/magenta]")

        for field_name, field_val in prov_settings.model_dump().items():
            if field_val is not None:
                display_val = field_val
                if field_name == "api_key" and field_val:
                    display_val = "******"
                prov_sub.add(f"{field_name}: [white]{display_val}[/white]")

    console.print(tree)


@config_app.command("set")
def set_value(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="The setting path (e.g. settings.theme or provider.openai.api_key)"),
    value: str = typer.Argument(..., help="The new value to assign"),
) -> None:
    """Set a configuration parameter dynamically, validating its type and saving to disk."""
    settings = ctx.obj.settings
    config_dir = ctx.obj.config_dir

    parts = key.split(".")
    if len(parts) < 2:
        typer.echo(
            "[bold red]Error:[/bold red] Key must be in format section.option "
            "or section.provider.option (e.g. 'settings.theme' or 'provider.openai.api_key').",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        # Traverse the object tree
        target = settings
        for part in parts[:-1]:
            if hasattr(target, part):
                target = getattr(target, part)
            else:
                typer.echo(f"[bold red]Error:[/bold red] Section '{part}' not found in configuration.", err=True)
                raise typer.Exit(code=1)

        # Retrieve parameter target field name
        field = parts[-1]
        if not hasattr(target, field):
            typer.echo(f"[bold red]Error:[/bold red] Option '{field}' not found in configuration.", err=True)
            raise typer.Exit(code=1)

        # Cast value based on Pydantic field annotation
        if isinstance(target, BaseModel):
            field_info = target.__class__.model_fields.get(field)
            if field_info is not None:
                annotation = field_info.annotation
                cast_val: Any = value
                
                if annotation is bool:
                    if value.lower() in ("true", "1", "yes"):
                        cast_val = True
                    elif value.lower() in ("false", "no", "0"):
                        cast_val = False
                    else:
                        typer.echo(f"[bold red]Error:[/bold red] Option '{field}' expects a boolean (true/false).", err=True)
                        raise typer.Exit(code=1)
                elif annotation is int:
                    if value.isdigit():
                        cast_val = int(value)
                    else:
                        typer.echo(f"[bold red]Error:[/bold red] Option '{field}' expects an integer.", err=True)
                        raise typer.Exit(code=1)
                elif annotation is float:
                    try:
                        cast_val = float(value)
                    except ValueError:
                        typer.echo(f"[bold red]Error:[/bold red] Option '{field}' expects a float.", err=True)
                        raise typer.Exit(code=1)
                elif value in ("", "''", '""'):
                    cast_val = None

                setattr(target, field, cast_val)

        # Re-validate the schema structure
        ZeroSettings(**settings.model_dump())

        # Save to disk
        save_config(settings, config_dir)
        typer.echo(f"[bold green]Success:[/bold green] Configured [cyan]{key}[/cyan] = [white]'{value}'[/white]")

    except (typer.Exit, typer.Abort):
        raise
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  - {loc}: {msg}")
        err_msg = "\n".join(errors)
        typer.echo(f"[bold red]Validation Error:[/bold red]\n{err_msg}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"[bold red]Unexpected Error:[/bold red] {e}", err=True)
        raise typer.Exit(code=1)
