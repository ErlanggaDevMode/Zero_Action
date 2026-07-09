"""CLI subcommand to benchmark the active AI provider's latency, TTFT, throughput, and cost."""

import time
import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from zero.services.ai import AIService
from zero.core.exceptions import ConfigError
import litellm

# Default test prompt for benchmarking
DEFAULT_BENCHMARK_PROMPT = "Write a 3-sentence greeting poem for a software developer."

def run_benchmark(
    ctx: typer.Context,
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model to benchmark"),
    prompt: str = typer.Option(DEFAULT_BENCHMARK_PROMPT, "--prompt", "-p", help="Prompt text used for the benchmark"),
) -> None:
    """Benchmark the active AI provider's performance and cost."""
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

    # Use specified model or fall back to provider's default model
    target_model = model or provider.model
    active_provider_name = settings.provider.active_provider

    console.print(Panel(
        f"Target Provider: [bold cyan]{active_provider_name}[/bold cyan]\n"
        f"Target Model:    [bold cyan]{target_model}[/bold cyan]\n"
        f"Benchmark Prompt: [dim]'{prompt}'[/dim]",
        title="[bold green]Zero Action - LLM Performance Benchmark[/bold green]",
        expand=False
    ))

    console.print("[yellow]Sending request and measuring latency...[/yellow]\n")

    start_time = time.time()
    ttft = 0.0
    chunks = []
    
    # We define an async function to run the stream
    async def run_stream():
        nonlocal ttft
        messages = [{"role": "user", "content": prompt}]
        first_chunk_received = False
        async for chunk in provider.stream(messages, model=target_model):
            if not first_chunk_received:
                ttft = time.time() - start_time
                first_chunk_received = True
            chunks.append(chunk)

    try:
        asyncio.run(run_stream())
    except Exception as e:
        console.print(f"[bold red]Benchmark failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    end_time = time.time()
    total_time = end_time - start_time
    full_response = "".join(chunks)

    # Calculate token counts
    prompt_tokens = provider.token_count(prompt)
    completion_tokens = provider.token_count(full_response)
    total_tokens = prompt_tokens + completion_tokens

    # Estimate cost using litellm
    clean_model = target_model
    if "/" in target_model:
        parts = target_model.split("/")
        if len(parts) > 2:
            clean_model = "/".join(parts[1:])
        else:
            clean_model = parts[-1]

    try:
        prompt_cost, completion_cost = litellm.cost_per_token(
            model=clean_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        total_cost = prompt_cost + completion_cost
    except Exception:
        # Fallback estimation
        total_cost = total_tokens * 0.00001

    # Render results
    table = Table(title="[bold green]Benchmark Results[/bold green]", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="green")

    table.add_row("Time to First Token (TTFT)", f"{ttft:.3f} s")
    table.add_row("Total Time", f"{total_time:.3f} s")
    table.add_row("Prompt Tokens", str(prompt_tokens))
    table.add_row("Completion Tokens", str(completion_tokens))
    table.add_row("Throughput", f"{completion_tokens / (total_time - ttft + 0.0001):.1f} tokens/sec" if total_time > ttft else "N/A")
    table.add_row("Estimated Cost", f"${total_cost:.6f}")

    console.print(table)
    console.print("\n[bold cyan]Response received:[/bold cyan]")
    console.print(Panel(full_response, border_style="dim"))
