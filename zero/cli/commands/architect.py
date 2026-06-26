"""CLI subcommand to compile requirements, load repository context, and generate system designs."""

import asyncio
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.markdown import Markdown
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError
from zero.services.logging import logger

async def stream_architect_response(provider, messages, console: Console) -> str:
    """Stream architect response and return the full content."""
    response_text = ""
    with Live(Markdown(response_text), console=console, auto_refresh=False) as live:
        async for chunk in provider.stream(messages):
            response_text += chunk
            live.update(Markdown(response_text), refresh=True)
    console.print()
    return response_text

def architect(
    ctx: typer.Context,
    requirements: str = typer.Option(None, "--requirements", "-r", help="Text description of the feature or architectural goals"),
    output: Path = typer.Option(Path("docs/architecture.md"), "--output", "-o", help="Target filepath to write the generated architecture design")
) -> None:
    """Generate a system architecture design document using AI and workspace context."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir
    
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        console.print("[yellow]Please run 'zero setup' first to configure your active provider.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error resolving AI provider:[/bold red] {e}")
        raise typer.Exit(code=1)

    resolved_requirements = requirements
    if not resolved_requirements:
        prd_file = Path("docs/prd.md")
        if prd_file.exists():
            try:
                resolved_requirements = prd_file.read_text(encoding="utf-8")
                console.print("[green]ℹ[/green] Loaded project requirements from [dim]docs/prd.md[/dim].")
            except Exception as e:
                logger.warning(f"Failed to read docs/prd.md: {e}")
                
    if not resolved_requirements:
        console.print("[bold yellow]Interactive Architecture Wizard[/bold yellow]")
        resolved_requirements = Prompt.ask("Describe the architectural goals or component details")
        
    if not resolved_requirements.strip():
        console.print("[bold red]Error:[/bold red] Architecture requirements cannot be empty.")
        raise typer.Exit(code=1)

    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "architect.md"
    architect_instructions = ""
    if prompt_file.exists():
        try:
            architect_instructions = prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read architect prompt template: {e}")
            
    if not architect_instructions:
        architect_instructions = "Generate a system architecture document in Markdown format."

    system_context = ai_service.get_system_prompt(Path.cwd())
    system_prompt = f"{system_context}\n\n{architect_instructions}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please generate a system architecture design based on these specifications: {resolved_requirements}"}
    ]

    console.print(f"\n[bold green]Zero Action Architect[/bold green] [dim]({provider.model})[/dim]")
    console.print("Generating Architecture Design Document...\n")

    try:
        arch_content = asyncio.run(stream_architect_response(provider, messages, console))
    except Exception as e:
        logger.bind(category="cli").error(f"Error during streaming architecture completion: {e}")
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(arch_content, encoding="utf-8")
        
        console.print(
            Panel(
                f"[bold green]✓ Architectural Design Complete![/bold green]\n"
                f"Design document successfully written to: [white]{output.resolve()}[/white]",
                title="[bold green]Success[/bold green]",
                border_style="green",
                expand=False
            )
        )
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to save architecture file: {e}")
        console.print(f"[bold red]Error saving architecture to file:[/bold red] {e}")
        raise typer.Exit(code=1)
