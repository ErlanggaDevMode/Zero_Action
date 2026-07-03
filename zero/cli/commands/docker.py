import time
import typer
import subprocess
from pathlib import Path
from rich.console import Console
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError

def docker(ctx: typer.Context) -> None:
    """Docker Auto-Pilot: generate container configurations, build, run, and self-heal run errors."""
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir
    
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        raise typer.Exit(code=1)
        
    cwd = Path.cwd().resolve()
    
    console.print("\n[bold green]Zero Action Docker Auto-Pilot[/bold green]")
    
    dockerfile_path = cwd / "Dockerfile"
    docker_compose_path = cwd / "docker-compose.yml"
    
    if not dockerfile_path.exists() or not docker_compose_path.exists():
        console.print("[yellow]Docker configuration files not found. Generating...[/yellow]")
        prompt = (
            "You are a DevOps assistant. Generate an optimized Dockerfile and a docker-compose.yml file "
            "for the active project. The project is a Python project. "
            "Return the configurations in two separate marked code blocks, clearly demarcated with "
            "### DOCKERFILE ### and ### DOCKER_COMPOSE ### headers."
        )
        
        try:
            raw_response = provider.chat([{"role": "user", "content": prompt}])
            
            if "### DOCKERFILE ###" in raw_response:
                dockerfile_part = raw_response.split("### DOCKERFILE ###")[1].split("###")[0].strip()
                if "```" in dockerfile_part:
                    dockerfile_part = dockerfile_part.split("```")[1].split("```")[0].strip()
                    if dockerfile_part.startswith("dockerfile") or dockerfile_part.startswith("Dockerfile"):
                        dockerfile_part = "\n".join(dockerfile_part.splitlines()[1:])
                dockerfile_path.write_text(dockerfile_part, encoding="utf-8")
                console.print("[green]✓ Generated Dockerfile[/green]")
                
            if "### DOCKER_COMPOSE ###" in raw_response:
                compose_part = raw_response.split("### DOCKER_COMPOSE ###")[1].split("###")[0].strip()
                if "```" in compose_part:
                    compose_part = compose_part.split("```")[1].split("```")[0].strip()
                    if compose_part.startswith("yaml") or compose_part.startswith("yml"):
                        compose_part = "\n".join(compose_part.splitlines()[1:])
                docker_compose_path.write_text(compose_part, encoding="utf-8")
                console.print("[green]✓ Generated docker-compose.yml[/green]")
        except Exception as e:
            console.print(f"[bold red]Failed to generate Docker configs:[/bold red] {e}")
            raise typer.Exit(code=1)
            
    console.print("[yellow]Building and starting containers using docker-compose...[/yellow]")
    build_res = subprocess.run(["docker", "compose", "up", "--build", "-d"], capture_output=True, text=True)
    if build_res.returncode != 0:
        console.print(f"[bold red]Docker compose build failed:[/bold red]\n{build_res.stderr}")
        raise typer.Exit(code=1)
        
    console.print("[green]Containers started successfully. Monitoring startup logs...[/green]")
    time.sleep(5)
    
    log_res = subprocess.run(["docker", "compose", "logs", "--tail=40"], capture_output=True, text=True)
    logs = log_res.stdout or log_res.stderr or ""
    
    if "Traceback" in logs or "Error" in logs or "exception" in logs.lower() or "failed" in logs.lower():
        console.print("[bold red]⚠️  Startup error detected in container logs![/bold red]")
        console.print(f"[dim red]Startup Logs:\n{logs}[/dim red]")
        
        console.print("[yellow]Querying AI self-healing fixer...[/yellow]")
        fix_prompt = (
            f"The docker container failed to start correctly. Here are the container logs:\n"
            f"```\n{logs}\n```\n\n"
            f"Analyze the logs and provide instructions or code changes to fix this startup issue."
        )
        try:
            suggested_fix = provider.chat([{"role": "user", "content": fix_prompt}])
            console.print("[bold cyan]AI suggested fix details:[/bold cyan]")
            console.print(suggested_fix)
            console.print("\n[yellow]Apply modifications manually or instruct the fixer to patch the repository.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Self-healing request failed:[/bold red] {e}")
    else:
        console.print("[bold green]✓ Docker container is running cleanly with no obvious errors in startup logs![/bold green]")
