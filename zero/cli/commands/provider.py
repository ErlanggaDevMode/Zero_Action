"""CLI commands to manage and configure multiple AI provider connection settings."""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from zero.providers.manager import ProviderManager
from zero.services.config import save_config

provider_app = typer.Typer(
    name="provider",
    help="[bold green]Zero Action Provider[/bold green]: Manage AI providers configurations.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

SUPPORTED_PROVIDERS = [
    "openai", "anthropic", "gemini", "openrouter", "ollama",
    "groq", "azure", "deepseek", "mistral", "compatible"
]

@provider_app.callback(invoke_without_command=True)
def default_callback(ctx: typer.Context) -> None:
    """Show currently active provider details if no subcommand is passed."""
    if ctx.invoked_subcommand is not None:
        return
        
    console = Console()
    settings = ctx.obj.settings
    active = settings.provider.active_provider
    
    if not active:
        console.print("[yellow]No active AI provider configured. Run 'zero setup' or 'zero provider list'.[/yellow]")
        return
        
    provider_defaults = getattr(settings.provider, active)
    console.print(
        Panel(
            f"Active Provider: [bold cyan]{active}[/bold cyan]\n"
            f"Model: [white]{provider_defaults.model}[/white]\n"
            f"Base URL: [dim]{provider_defaults.base_url}[/dim]",
            title="[bold green]Current Active Provider[/bold green]",
            border_style="green",
            expand=False
        )
    )

@provider_app.command("list")
def list_providers(ctx: typer.Context) -> None:
    """List all supported providers and their configuration status."""
    console = Console()
    settings = ctx.obj.settings
    active = settings.provider.active_provider
    
    table = Table(title="[bold green]Supported AI Providers[/bold green]", show_header=True, header_style="bold cyan")
    table.add_column("Provider Name", style="bold white")
    table.add_column("Configured", justify="center")
    table.add_column("Status", justify="center")
    
    for p in SUPPORTED_PROVIDERS:
        provider_defaults = getattr(settings.provider, p)
        is_configured = "Yes"
        if p != "ollama" and not provider_defaults.api_key:
            is_configured = "[dim]No[/dim]"
            
        status_str = ""
        if p == active:
            status_str = "[bold green]Active[/bold green]"
            
        table.add_row(p, is_configured, status_str)
        
    console.print(table)

@provider_app.command("add")
def add_provider(
    ctx: typer.Context,
    provider_name: str = typer.Argument(..., help="Name of the provider to configure (e.g. openai, gemini)")
) -> None:
    """Configure a specific AI provider settings."""
    console = Console()
    settings = ctx.obj.settings
    config_dir = ctx.obj.config_dir
    
    provider_name = provider_name.lower()
    if provider_name not in SUPPORTED_PROVIDERS:
        console.print(f"[bold red]Error:[/bold red] Unsupported provider: '{provider_name}'")
        raise typer.Exit(code=1)
        
    provider_defaults = getattr(settings.provider, provider_name)
    default_base_url = provider_defaults.base_url or ""
    default_model = provider_defaults.model or ""
    
    api_key = None
    if provider_name != "ollama":
        current_key = provider_defaults.api_key
        if current_key:
            api_key = Prompt.ask(
                f"Enter API Key for {provider_name} (press Enter to keep existing)",
                password=True,
                default=current_key,
                show_default=False,
            )
        else:
            api_key = Prompt.ask(f"Enter API Key for {provider_name}", password=True, default="")
            
        if api_key == "":
            api_key = None

    base_url = Prompt.ask(f"Enter Base URL for {provider_name}", default=default_base_url)
    if base_url == "":
        base_url = None

    model = Prompt.ask(f"Enter Model Name for {provider_name}", default=default_model)

    provider_defaults.api_key = api_key
    provider_defaults.base_url = base_url
    provider_defaults.model = model

    manager = ProviderManager(settings)
    try:
        provider_instance = manager.get_provider(provider_name)
    except Exception as e:
        console.print(f"[bold red]Failed to load configuration:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print("\n[bold yellow]Testing connection to provider...[/bold yellow]")
    with console.status("[bold green]Sending ping request...[/bold green]"):
        connection_ok = provider_instance.health_check()

    if connection_ok:
        console.print("[bold green]✓ Connection successful![/bold green]")
    else:
        console.print("[bold red]✗ Connection check failed.[/bold red]")
        save_anyway = Confirm.ask("Would you like to save this configuration anyway?", default=False)
        if not save_anyway:
            console.print("[yellow]Configuration was not saved.[/yellow]")
            raise typer.Exit(code=1)

    settings.provider.active_provider = provider_name
    save_config(settings, config_dir)
    console.print(f"[green]✓[/green] Provider [bold cyan]{provider_name}[/bold cyan] configured successfully and set as active.")

@provider_app.command("remove")
def remove_provider(
    ctx: typer.Context,
    provider_name: str = typer.Argument(..., help="Name of the provider to remove configuration from")
) -> None:
    """Clear configuration details for a specific provider."""
    console = Console()
    settings = ctx.obj.settings
    config_dir = ctx.obj.config_dir
    
    provider_name = provider_name.lower()
    if provider_name not in SUPPORTED_PROVIDERS:
        console.print(f"[bold red]Error:[/bold red] Unsupported provider: '{provider_name}'")
        raise typer.Exit(code=1)
        
    confirm = Confirm.ask(f"Are you sure you want to clear configurations for '{provider_name}'?", default=False)
    if not confirm:
        console.print("[yellow]Aborted.[/yellow]")
        return
        
    provider_defaults = getattr(settings.provider, provider_name)
    provider_defaults.api_key = None
    
    if settings.provider.active_provider == provider_name:
        settings.provider.active_provider = ""
        
    save_config(settings, config_dir)
    console.print(f"[green]✓[/green] Cleared configurations for provider [bold cyan]{provider_name}[/bold cyan].")

@provider_app.command("switch")
def switch_provider(
    ctx: typer.Context,
    provider_name: str = typer.Argument(..., help="Name of the provider to set as active")
) -> None:
    """Switch active AI provider configuration."""
    console = Console()
    settings = ctx.obj.settings
    config_dir = ctx.obj.config_dir
    
    provider_name = provider_name.lower()
    if provider_name not in SUPPORTED_PROVIDERS:
        console.print(f"[bold red]Error:[/bold red] Unsupported provider: '{provider_name}'")
        raise typer.Exit(code=1)
        
    provider_defaults = getattr(settings.provider, provider_name)
    if provider_name != "ollama" and not provider_defaults.api_key:
        console.print(f"[bold yellow]Warning:[/bold yellow] Provider '{provider_name}' is not configured yet. Run 'zero provider add {provider_name}' to set it up.")
        raise typer.Exit(code=1)
        
    settings.provider.active_provider = provider_name
    save_config(settings, config_dir)
    console.print(f"[green]✓[/green] Active provider successfully switched to [bold cyan]{provider_name}[/bold cyan].")

@provider_app.command("models")
def list_models(
    ctx: typer.Context,
    provider_name: Optional[str] = typer.Argument(None, help="Name of the provider to list models for (defaults to active provider)")
) -> None:
    """Display supported models list for a provider."""
    console = Console()
    settings = ctx.obj.settings
    
    p_name = provider_name or settings.provider.active_provider
    if not p_name:
        console.print("[bold red]Error:[/bold red] No active provider configured, please specify a provider name.")
        raise typer.Exit(code=1)
        
    p_name = p_name.lower()
    manager = ProviderManager(settings)
    try:
        provider_instance = manager.get_provider(p_name)
        models = provider_instance.list_models()
        console.print(f"\n[bold green]Models for provider {p_name}:[/bold green]")
        for m in models:
            console.print(f" - {m}")
    except Exception as e:
        console.print(f"[bold red]Error listing models for provider '{p_name}':[/bold red] {e}")
        raise typer.Exit(code=1)

@provider_app.command("test")
def test_provider(
    ctx: typer.Context,
    provider_name: Optional[str] = typer.Argument(None, help="Name of the provider to test (defaults to active provider)")
) -> None:
    """Run connection health check test for a provider."""
    console = Console()
    settings = ctx.obj.settings
    
    p_name = provider_name or settings.provider.active_provider
    if not p_name:
        console.print("[bold red]Error:[/bold red] No active provider configured, please specify a provider name.")
        raise typer.Exit(code=1)
        
    p_name = p_name.lower()
    manager = ProviderManager(settings)
    try:
        provider_instance = manager.get_provider(p_name)
        console.print(f"\n[bold yellow]Testing connection to provider '{p_name}'...[/bold yellow]")
        with console.status("[bold green]Sending ping request...[/bold green]"):
            ok = provider_instance.health_check()
        if ok:
            console.print(f"[bold green]✓ Provider '{p_name}' is healthy and connected.[/bold green]")
        else:
            console.print(f"[bold red]✗ Provider '{p_name}' connection failed.[/bold red]")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error testing provider '{p_name}':[/bold red] {e}")
        raise typer.Exit(code=1)
