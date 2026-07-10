"""CLI subcommand to perform AI-powered code review on source files or directories."""

import asyncio
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from zero.core.ui import stream_completion_with_timer
from zero.services.logging import logger

if TYPE_CHECKING:
    from zero.services.ai import AIService



_VALID_FOCUS_AREAS = {
    "security",
    "performance",
    "maintainability",
    "scalability",
    "readability",
}

_DEFAULT_FOCUS = "security,performance,maintainability,scalability,readability"




def _build_messages(
    ai_service: AIService,
    reviewer_instructions: str,
    file_path: Path,
    file_content: str,
    focus_areas: list[str],
) -> list[dict[str, str]]:
    """Construct the message list for a single file review."""
    system_context = ai_service.get_system_prompt(Path.cwd())
    focus_note = (
        f"Focus your review only on these concern areas: {', '.join(focus_areas)}."
        if len(focus_areas) < len(_VALID_FOCUS_AREAS)
        else ""
    )
    system_prompt = f"{system_context}\n\n{reviewer_instructions}"
    if focus_note:
        system_prompt += f"\n\n{focus_note}"

    user_prompt = (
        f"Please review the following source file.\n\n"
        f"File: {file_path}\n\n"
        f"```\n{file_content}\n```"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _collect_files(target_dir: Path) -> list[Path]:
    """Return all readable source files from a directory (non-recursive hidden dirs excluded)."""
    extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".cs",
        ".rs", ".cpp", ".c", ".h", ".rb", ".php", ".swift", ".kt",
        ".sh", ".yaml", ".yml", ".toml", ".json",
    }
    collected: list[Path] = []
    for path in sorted(target_dir.rglob("*")):
        # Skip hidden dirs (e.g. .git, .venv, __pycache__)
        if any(part.startswith((".", "__")) for part in path.parts):
            continue
        if path.is_file() and path.suffix in extensions:
            collected.append(path)
    return collected


def review(
    ctx: typer.Context,
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Source file to review"),
    dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Directory of source files to review"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save the review report to this file"),
    focus: str = typer.Option(
        _DEFAULT_FOCUS,
        "--focus",
        help="Comma-separated focus areas: security,performance,maintainability,scalability,readability",
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model override to delegate specific task execution"),
    vision: bool = typer.Option(False, "--vision", "-v", help="Perform a visual UI/UX review of an image mockup"),
) -> None:
    """Perform an AI-powered code review on a file or directory of source files."""
    from zero.services.ai import AIService
    from zero.core.exceptions import ConfigError
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # -- Provider setup -------------------------------------------------------
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

    if vision:
        if not file:
            console.print("[bold red]Error:[/bold red] Please specify an image file to review (e.g. zero review --vision -f mockup.png).")
            raise typer.Exit(code=1)
        if not file.exists():
            console.print(f"[bold red]Error:[/bold red] File '{file}' not found.")
            raise typer.Exit(code=1)
            
        import base64
        ext = file.suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            console.print(f"[bold red]Error:[/bold red] File '{file}' is not a supported image format (.png, .jpg, .jpeg, .webp).")
            raise typer.Exit(code=1)
            
        try:
            image_data = file.read_bytes()
            mime_type = f"image/{ext[1:]}" if ext != ".jpg" else "image/jpeg"
            base64_image = base64.b64encode(image_data).decode("utf-8")
        except Exception as e:
            console.print(f"[bold red]Error reading image file:[/bold red] {e}")
            raise typer.Exit(code=1)
            
        console.print(f"\n[bold green]Zero Action Visual UI/UX Reviewer[/bold green] [dim]({provider.model})[/dim]")
        console.print(f"Reviewing image [dim]{file}[/dim]...\n")
        
        system_prompt = (
            "You are an expert UI/UX design auditor and frontend engineer. "
            "Analyze the layout, alignment, colors, typography, contrast, accessibility, and responsiveness of this UI mockup. "
            "Generate a professional, structured markdown review report and suggest corresponding CSS/HTML fixes or improvements."
        )
        user_content = [
            {"type": "text", "text": "Please perform a visual UI/UX design audit on this mockup image."},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            }
        ]
        vision_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        target_model = model or provider.model
        try:
            kwargs = {}
            if target_model:
                kwargs["model"] = target_model
            review_text = asyncio.run(stream_completion_with_timer(provider, vision_messages, console, **kwargs))
        except Exception as e:
            console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
            raise typer.Exit(code=1)
            
        if output:
            try:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(review_text, encoding="utf-8")
                console.print(Panel(f"[bold green]✓ Visual Review Complete![/bold green]\nReport saved to: [white]{output.resolve()}[/white]"))
            except Exception as e:
                console.print(f"[bold red]Error saving review report:[/bold red] {e}")
                raise typer.Exit(code=1)
        return

    # -- Focus area validation ------------------------------------------------
    requested_areas = [a.strip().lower() for a in focus.split(",") if a.strip()]
    invalid_areas = set(requested_areas) - _VALID_FOCUS_AREAS
    if invalid_areas:
        console.print(
            f"[bold red]Error:[/bold red] Unknown focus area(s): {', '.join(sorted(invalid_areas))}.\n"
            f"Valid options: {', '.join(sorted(_VALID_FOCUS_AREAS))}"
        )
        raise typer.Exit(code=1)
    focus_areas = requested_areas if requested_areas else list(_VALID_FOCUS_AREAS)

    # -- Target file(s) resolution --------------------------------------------
    target_files: list[Path] = []

    if file and dir:
        console.print("[bold red]Error:[/bold red] Use either --file or --dir, not both.")
        raise typer.Exit(code=1)

    if file:
        if not file.exists():
            console.print(f"[bold red]Error:[/bold red] File '{file}' not found.")
            raise typer.Exit(code=1)
        if not file.is_file():
            console.print(f"[bold red]Error:[/bold red] '{file}' is not a file.")
            raise typer.Exit(code=1)
        target_files = [file]

    elif dir:
        if not dir.exists():
            console.print(f"[bold red]Error:[/bold red] Directory '{dir}' not found.")
            raise typer.Exit(code=1)
        if not dir.is_dir():
            console.print(f"[bold red]Error:[/bold red] '{dir}' is not a directory.")
            raise typer.Exit(code=1)
        target_files = _collect_files(dir)
        if not target_files:
            console.print(f"[yellow]No reviewable source files found in '{dir}'.[/yellow]")
            raise typer.Exit(code=0)
        console.print(
            f"[green]ℹ[/green] Found [bold]{len(target_files)}[/bold] file(s) to review in [dim]{dir}[/dim]."
        )

    else:
        # Interactive fallback: ask for a file path
        console.print("[bold yellow]Interactive Review Wizard[/bold yellow]")
        file_input = Prompt.ask("Enter the path to the file you want to review")
        if not file_input.strip():
            console.print("[bold red]Error:[/bold red] File path cannot be empty.")
            raise typer.Exit(code=1)
        resolved = Path(file_input.strip())
        if not resolved.exists():
            console.print(f"[bold red]Error:[/bold red] File '{resolved}' not found.")
            raise typer.Exit(code=1)
        target_files = [resolved]

    # -- Load reviewer prompt template ----------------------------------------
    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "reviewer.md"
    reviewer_instructions = ""
    if prompt_file.exists():
        try:
            reviewer_instructions = prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read reviewer prompt template: {e}")

    if not reviewer_instructions:
        reviewer_instructions = (
            "You are a professional code reviewer. "
            "Review the provided source file and produce structured Markdown feedback "
            "covering security, performance, maintainability, scalability, and readability."
        )

    # -- Review each file -----------------------------------------------------
    all_reviews: list[str] = []

    console.print(f"\n[bold green]Zero Action Reviewer[/bold green] [dim]({provider.model})[/dim]")
    if len(focus_areas) < len(_VALID_FOCUS_AREAS):
        console.print(f"Focus: [cyan]{', '.join(focus_areas)}[/cyan]")

    for idx, target_file in enumerate(target_files, start=1):
        if len(target_files) > 1:
            console.print(f"\n[dim]── Reviewing [{idx}/{len(target_files)}]: {target_file} ──[/dim]")
        else:
            console.print(f"Reviewing [dim]{target_file}[/dim]...\n")

        try:
            file_content = target_file.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error reading '{target_file}':[/bold red] {e}")
            logger.bind(category="cli").error(f"Failed to read file for review: {target_file}: {e}")
            continue

        messages = _build_messages(ai_service, reviewer_instructions, target_file, file_content, focus_areas)

        target_model = model
        if not target_model:
            clean_focus = [f.strip().lower() for f in focus.split(",")]
            if len(clean_focus) == 1 and clean_focus[0] == "readability":
                target_model = "gemini/gemini-2.0-flash"

        try:
            kwargs = {}
            if target_model:
                kwargs["model"] = target_model
            review_text = asyncio.run(stream_completion_with_timer(provider, messages, console, **kwargs))
            all_reviews.append(review_text)
        except Exception as e:
            logger.bind(category="cli").error(f"Error during streaming review for {target_file}: {e}")
            console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    if not all_reviews:
        console.print("[yellow]No reviews were generated.[/yellow]")
        raise typer.Exit(code=0)

    # -- Save output if requested ---------------------------------------------
    if output:
        combined_review = "\n\n---\n\n".join(all_reviews)

        if output.exists():
            console.print(f"[yellow]⚠️  Warning: File [bold]{output}[/bold] already exists.[/yellow]")
            confirm = Confirm.ask("Do you want to overwrite it?", default=False)
            if not confirm:
                console.print("[yellow]Skipped saving review.[/yellow]")
                raise typer.Exit(code=0)

        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(combined_review, encoding="utf-8")
            console.print(
                Panel(
                    f"[bold green]✓ Review Complete![/bold green]\n"
                    f"Report saved to: [white]{output.resolve()}[/white]",
                    title="[bold green]Success[/bold green]",
                    border_style="green",
                    expand=False,
                )
            )
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to save review report: {e}")
            console.print(f"[bold red]Error saving review report:[/bold red] {e}")
            raise typer.Exit(code=1)
    else:
        console.print(
            Panel(
                f"[bold green]✓ Review Complete![/bold green]\n"
                f"Reviewed [bold]{len(all_reviews)}[/bold] file(s).",
                title="[bold green]Success[/bold green]",
                border_style="green",
                expand=False,
            )
        )
