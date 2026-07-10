"""CLI subcommand to auto-detect tech stack and generate VS Code Dev Container configurations."""

import re
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError

def generate_devcontainer(ctx: typer.Context) -> None:
    """Detect workspace technology stack and generate Dev Container configurations."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # 1. Detect technology stack
    workspace = Path.cwd()
    languages = set()
    frameworks = set()

    for path in workspace.rglob("*"):
        if any(part.startswith((".", "__")) for part in path.parts):
            continue
        if path.is_file():
            ext = path.suffix.lower()
            if ext == ".py":
                languages.add("Python")
            elif ext in (".js", ".jsx", ".ts", ".tsx"):
                languages.add("JavaScript/TypeScript")
            elif ext == ".go":
                languages.add("Go")
            elif ext == ".rs":
                languages.add("Rust")
            elif ext == ".java":
                languages.add("Java")
                
            # Framework files
            if path.name == "requirements.txt" or path.name == "pyproject.toml":
                frameworks.add("Python dependencies")
            elif path.name == "package.json":
                frameworks.add("Node.js/NPM")
            elif path.name == "go.mod":
                frameworks.add("Go modules")
            elif path.name == "Cargo.toml":
                frameworks.add("Rust Cargo")

    lang_desc = ", ".join(languages) or "Generic"
    fw_desc = ", ".join(frameworks) or "None detected"

    console.print(f"[cyan]Detected Stack: [bold]{lang_desc}[/bold][/cyan]")
    console.print(f"Detected Build Files: [bold]{fw_desc}[/bold]\n")

    # 2. Query LLM to generate devcontainer files
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        raise typer.Exit(code=1)

    console.print("[yellow]Designing Dev Container configurations...[/yellow]")
    
    system_prompt = (
        "You are an expert devops engineer. Generate the content of two configuration files for VS Code Dev Containers:\n"
        "1. devcontainer.json\n"
        "2. Dockerfile\n\n"
        "Format the output using exact markdown blocks with file headers:\n\n"
        "File: devcontainer.json\n"
        "```json\n"
        "...\n"
        "```\n\n"
        "File: Dockerfile\n"
        "```dockerfile\n"
        "...\n"
        "```"
    )
    user_prompt = f"Workspace technology stack: {lang_desc}\nBuild framework files: {fw_desc}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response_text = provider.chat(messages)
    except Exception as e:
        console.print(f"[bold red]AI Generation failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 3. Parse files from response
    devcontainer_json = ""
    dockerfile = ""

    # Parse devcontainer.json
    json_match = re.search(r"File:\s*devcontainer\.json\s*```(?:json)?\n(.*?)\n```", response_text, re.DOTALL | re.IGNORECASE)
    if json_match:
        devcontainer_json = json_match.group(1).strip()

    # Parse Dockerfile
    dockerfile_match = re.search(r"File:\s*Dockerfile\s*```(?:dockerfile)?\n(.*?)\n```", response_text, re.DOTALL | re.IGNORECASE)
    if dockerfile_match:
        dockerfile = dockerfile_match.group(1).strip()

    if not devcontainer_json or not dockerfile:
        # Fallback regex in case formatting was slightly off
        fallback_json = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        fallback_docker = re.search(r"```(?:dockerfile)?\n(.*?)\n```", response_text, re.DOTALL)
        if fallback_json:
            devcontainer_json = fallback_json.group(1).strip()
        if fallback_docker:
            dockerfile = fallback_docker.group(1).strip()

    if not devcontainer_json or not dockerfile:
        console.print("[bold red]Error:[/bold red] AI output was malformed. Could not separate devcontainer.json and Dockerfile.")
        console.print(response_text)
        raise typer.Exit(code=1)

    # 4. Write files
    devcontainer_dir = workspace / ".devcontainer"
    try:
        devcontainer_dir.mkdir(exist_ok=True)
        (devcontainer_dir / "devcontainer.json").write_text(devcontainer_json, encoding="utf-8")
        (devcontainer_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8")
        
        console.print(Panel(
            "[bold green]✓ Dev Container configuration files created successfully![/bold green]\n\n"
            "- Saved [white].devcontainer/devcontainer.json[/white]\n"
            "- Saved [white].devcontainer/Dockerfile[/white]",
            title="[bold green]Dev Container Auto-Gen[/bold green]"
        ))
    except Exception as e:
        console.print(f"[bold red]Failed to write files:[/bold red] {e}")
        raise typer.Exit(code=1)
