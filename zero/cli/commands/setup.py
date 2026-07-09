import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from zero.providers.manager import ProviderManager
from zero.services.config import save_config



def setup(ctx: typer.Context) -> None:
    """Run the interactive wizard to set up your AI Provider and connection."""
    settings = ctx.obj.settings
    config_dir = ctx.obj.config_dir

    console = Console()

    # Welcome Banner Panel
    console.print(
        Panel(
            "[bold cyan]Welcome to the Zero Action Setup Wizard![/bold cyan]\n"
            "This wizard will configure your active AI provider and verify the connection settings.",
            title="[bold green]Zero Action Setup[/bold green]",
            border_style="green",
        )
    )

    # 1. Provider Selection
    choices = [
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
        "nvidia",
        "alibaba",
        "bedrock",
        "vertex",
        "opencode",
        "opencode_zen",
    ]
    
    active_default = settings.provider.active_provider or "openai"
    provider_name = Prompt.ask(
        "Select AI Provider",
        choices=choices,
        default=active_default,
    )
    provider_name = provider_name.lower()

    # 2. Retrieve Defaults for the Selected Provider
    provider_defaults = getattr(settings.provider, provider_name)
    default_base_url = provider_defaults.base_url or ""
    default_model = provider_defaults.model or ""

    # 3. Prompt for API Key (ignored for local Ollama)
    api_key = None
    if provider_name != "ollama":
        current_key = provider_defaults.api_key
        if current_key:
            api_key = Prompt.ask(
                "Enter API Key (press Enter to keep existing)",
                default=current_key,
                show_default=False,
            )
        else:
            api_key = Prompt.ask("Enter API Key", default="")


            
        if api_key == "":
            api_key = None

    # 4. Prompt for Base URL
    base_url = Prompt.ask("Enter Base URL", default=default_base_url)
    if base_url == "":
        base_url = None

    # 5. Prompt for Model Name
    model = Prompt.ask("Enter Model Name", default=default_model)

    # 6. Apply Settings Temporarily for Testing
    provider_defaults.api_key = api_key
    provider_defaults.base_url = base_url
    provider_defaults.model = model

    # Instantiate Provider using Manager
    manager = ProviderManager(settings)
    
    try:
        provider_instance = manager.get_provider(provider_name)
    except Exception as e:
        Console(stderr=True).print(f"[bold red]Failed to load provider configuration details:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 7. Test Connection (Health Check)
    console.print("\n[bold yellow]Testing connection to provider...[/bold yellow]")
    
    with console.status("[bold green]Sending ping request...[/bold green]"):
        connection_ok = provider_instance.health_check()

    if connection_ok:
        console.print("[bold green]✓ Connection successful![/bold green]")
    else:
        console.print("[bold red]✗ Connection check failed.[/bold red]")
        save_anyway = Confirm.ask(
            "Would you like to save this configuration anyway?",
            default=False,
        )
        if not save_anyway:
            console.print("[yellow]Setup aborted. Configuration was not saved.[/yellow]")
            raise typer.Exit(code=1)

    # 8. Commit Active Provider and Save Configs
    settings.provider.active_provider = provider_name
    save_config(settings, config_dir)

    console.print(
        Panel(
            f"[bold green]Zero Action Setup Complete![/bold green]\n"
            f"Active Provider: [cyan]{provider_name}[/cyan]\n"
            f"Model: [white]{model}[/white]\n"
            f"Configuration persisted to: [white]{config_dir}[/white]",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )
