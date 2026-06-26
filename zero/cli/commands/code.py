"""CLI subcommand to compile requirements, load repository context, and generate source code files via AI."""

import asyncio
import re
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.live import Live
from rich.markdown import Markdown
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError
from zero.services.logging import logger

async def stream_code_response(provider, messages, console: Console) -> str:
    """Stream coder response and return the full content."""
    response_text = ""
    with Live(Markdown(response_text), console=console, auto_refresh=False) as live:
        async for chunk in provider.stream(messages):
            response_text += chunk
            live.update(Markdown(response_text), refresh=True)
    console.print()
    return response_text

def parse_coder_response(response_text: str) -> tuple[str | None, str]:
    """Parse the file path and code content from the AI response."""
    # Look for a line starting with "File:" or "File path:" (case-insensitive)
    file_match = re.search(r'(?i)(?:^|\n)[*\s`_-]*file(?:[ -]path)?:[*\s`_-]*([^\n\r]+)', response_text)
    file_path = None
    if file_match:
        raw_path = file_match.group(1).strip()
        # strip common brackets/ticks/quotes
        raw_path = re.sub(r'^[`"\'<\[\s]+|[`"\'\>\]\s]+$', '', raw_path)
        # make sure it looks like a path - allow ':' only for Windows drive letters (e.g. "C:/")
        invalid_chars = set(' *?|<>"\'')
        # Detect colons that are NOT a Windows drive-letter separator (letter followed by ':')
        has_invalid_colon = False
        if ':' in raw_path:
            # Allow at most one colon at position 1 (Windows drive), e.g. "C:/path"
            colon_indices = [i for i, c in enumerate(raw_path) if c == ':']
            for idx in colon_indices:
                if not (idx == 1 and raw_path[0].isalpha()):
                    has_invalid_colon = True
                    break
        if raw_path and not any(c in raw_path for c in invalid_chars) and not has_invalid_colon:
            file_path = raw_path

    # Try to extract the first code block (e.g. ```python ... ```)

    code_block_match = re.search(r'```[a-zA-Z0-9_\-\+]*\n(.*?)```', response_text, re.DOTALL)
    if code_block_match:
        code_content = code_block_match.group(1)
    else:
        # If no code block, use the whole text (minus the File: line if present)
        code_content = response_text
        if file_match:
            # remove the File: ... line
            code_content = re.sub(r'(?i)(?:^|\n)[*\s`_-]*file(?:[ -]path)?:[^\n\r]*', '', code_content, count=1).strip()
            
    return file_path, code_content

def code(
    ctx: typer.Context,
    requirements: str = typer.Option(None, "--requirements", "-r", help="Text description of the coding goal or task"),
    output: Path = typer.Option(None, "--output", "-o", help="Target filepath to write the generated code"),
    spec: Path = typer.Option(None, "--spec", "-s", help="Path to specification file to load context from")
) -> None:
    """Generate or update project source files using AI and workspace context."""
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

    # 1. Load context from specifications
    spec_content = ""
    if spec:
        if spec.exists():
            try:
                spec_content = spec.read_text(encoding="utf-8")
                console.print(f"[green]ℹ[/green] Loaded specification context from [dim]{spec}[/dim].")
            except Exception as e:
                logger.warning(f"Failed to read spec file {spec}: {e}")
        else:
            console.print(f"[bold red]Error:[/bold red] Specification file '{spec}' not found.")
            raise typer.Exit(code=1)
    else:
        # Check defaults if spec option not passed: docs/prd.md and docs/architecture.md
        prd_file = Path("docs/prd.md")
        arch_file = Path("docs/architecture.md")
        
        loaded_specs = []
        if prd_file.exists():
            try:
                spec_content += f"\n--- PRD ---\n{prd_file.read_text(encoding='utf-8')}\n"
                loaded_specs.append("docs/prd.md")
            except Exception as e:
                logger.warning(f"Failed to read docs/prd.md: {e}")
                
        if arch_file.exists():
            try:
                spec_content += f"\n--- ARCHITECTURE ---\n{arch_file.read_text(encoding='utf-8')}\n"
                loaded_specs.append("docs/architecture.md")
            except Exception as e:
                logger.warning(f"Failed to read docs/architecture.md: {e}")
                
        if loaded_specs:
            console.print(f"[green]ℹ[/green] Loaded specification context from: [dim]{', '.join(loaded_specs)}[/dim].")

    # 2. Get requirements or prompt user
    resolved_requirements = requirements
    if not resolved_requirements:
        if spec_content:
            resolved_requirements = Prompt.ask("Describe the implementation goals or target file to generate based on specs")
        else:
            console.print("[bold yellow]Interactive Coding Wizard[/bold yellow]")
            resolved_requirements = Prompt.ask("Describe the coding goal or the file you want to generate")

    if not resolved_requirements or not resolved_requirements.strip():
        console.print("[bold red]Error:[/bold red] Coding requirements cannot be empty.")
        raise typer.Exit(code=1)

    # 3. Read prompt instructions from zero/prompts/coder.md
    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "coder.md"
    coder_instructions = ""
    if prompt_file.exists():
        try:
            coder_instructions = prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read coder prompt template: {e}")
            
    if not coder_instructions:
        coder_instructions = (
            "Generate production-ready code with type annotations and error handling. "
            "Never output placeholders. "
            "If target file path is not given, output it on a line starting with 'File: '."
        )

    # 4. Compile messages
    system_context = ai_service.get_system_prompt(Path.cwd())
    system_prompt = f"{system_context}\n\n{coder_instructions}"
    
    user_prompt = ""
    if spec_content:
        user_prompt += f"Project Specifications:\n{spec_content}\n\n"
    user_prompt += f"Task / Requirements:\n{resolved_requirements}\n"
    if output:
        user_prompt += f"\nWrite code specifically for file: {output}\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    console.print(f"\n[bold green]Zero Action Coder[/bold green] [dim]({provider.model})[/dim]")
    console.print("Generating project source code...\n")

    # 5. Get LLM response
    try:
        response_text = asyncio.run(stream_code_response(provider, messages, console))
    except Exception as e:
        logger.bind(category="cli").error(f"Error during streaming code completion: {e}")
        console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 6. Parse response to extract file path and code content
    parsed_path_str, code_content = parse_coder_response(response_text)
    
    # Target file path determination
    final_output = output
    if not final_output:
        if parsed_path_str:
            final_output = Path(parsed_path_str)
        else:
            path_input = Prompt.ask("No target file path found in AI response. Please specify a filepath to write")
            if not path_input.strip():
                console.print("[bold red]Error:[/bold red] Filepath cannot be empty.")
                raise typer.Exit(code=1)
            final_output = Path(path_input.strip())

    # Check for overwrite protection
    if final_output.exists():
        console.print(f"[yellow]⚠️ Warning: File [bold]{final_output}[/bold] already exists.[/yellow]")
        confirm = Confirm.ask("Do you want to overwrite it?", default=False)
        if not confirm:
            console.print("[yellow]Skipped writing file.[/yellow]")
            raise typer.Exit(code=0)

    # 7. Write to file
    try:
        final_output.parent.mkdir(parents=True, exist_ok=True)
        final_output.write_text(code_content, encoding="utf-8")
        
        console.print(
            Panel(
                f"[bold green]✓ Code Generation Complete![/bold green]\n"
                f"Source file successfully written to: [white]{final_output.resolve()}[/white]",
                title="[bold green]Success[/bold green]",
                border_style="green",
                expand=False
            )
        )
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to save generated code file: {e}")
        console.print(f"[bold red]Error saving code to file:[/bold red] {e}")
        raise typer.Exit(code=1)
