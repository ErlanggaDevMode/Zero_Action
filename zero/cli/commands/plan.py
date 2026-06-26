"""CLI subcommand to compile requirements, load repository context, and generate PRDs via AI."""

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

async def stream_plan_response(provider, messages, console: Console) -> str:
    """Stream plan response and return the full content."""
    response_text = ""
    with Live(Markdown(response_text), console=console, auto_refresh=False) as live:
        async for chunk in provider.stream(messages):
            response_text += chunk
            live.update(Markdown(response_text), refresh=True)
    console.print()
    return response_text

def plan(
    ctx: typer.Context,
    requirements: str = typer.Option(None, "--requirements", "-r", help="Text description of the feature or project requirements"),
    output: Path = typer.Option(Path("docs/prd.md"), "--output", "-o", help="Target filepath to write the generated PRD markdown")
) -> None:
    """Generate a Product Requirement Document (PRD) using AI and workspace context."""
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

    if not requirements:
        console.print("[bold yellow]Interactive Planning Wizard[/bold yellow]")
        requirements = Prompt.ask("Describe the feature or project requirements you want to plan")
        
    if not requirements.strip():
        console.print("[bold red]Error:[/bold red] Requirements description cannot be empty.")
        raise typer.Exit(code=1)

    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "planner.md"
    planner_instructions = ""
    if prompt_file.exists():
        try:
            planner_instructions = prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read planner prompt template: {e}")
            
    if not planner_instructions:
        planner_instructions = "Generate a Product Requirement Document (PRD) in Markdown format."

    system_context = ai_service.get_system_prompt(Path.cwd())
    system_prompt = f"{system_context}\n\n{planner_instructions}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please generate a PRD based on these requirements: {requirements}"}
    ]

    console.print(f"\n[bold green]Zero Action Planner[/bold green] [dim]({provider.model})[/dim]")
    console.print("Generating Product Requirement Document (PRD)...\n")

    try:
        prd_content = asyncio.run(stream_plan_response(provider, messages, console))
    except Exception as e:
        logger.bind(category="cli").error(f"Error during streaming plan completion: {e}")
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(prd_content, encoding="utf-8")
        
        console.print(
            Panel(
                f"[bold green]✓ Planning Complete![/bold green]\n"
                f"PRD successfully written to: [white]{output.resolve()}[/white]",
                title="[bold green]Success[/bold green]",
                border_style="green",
                expand=False
            )
        )
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to save PRD file: {e}")
        console.print(f"[bold red]Error saving PRD to file:[/bold red] {e}")
        raise typer.Exit(code=1)
