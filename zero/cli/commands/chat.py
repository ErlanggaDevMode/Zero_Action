"""CLI subcommand for interactive terminal conversation loops with memory tracking."""

import asyncio
import os
import shlex
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
import typer


from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text


from zero.services.ai import AIService
from zero.memory.manager import MemoryManager
from zero.core.exceptions import ConfigError
from zero.services.logging import logger

# Command dispatch handlers will lazy-import their respective subcommands



from zero.core.ui import stream_completion_with_timer



def parse_slash_args(cmd_args: str) -> tuple[dict[str, str], str]:
    """Parse slash command arguments into options and remaining requirements text."""
    try:
        parts = shlex.split(cmd_args)
    except Exception:
        parts = cmd_args.split()

    opts = {}
    req_parts = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ("-o", "--output") and i + 1 < len(parts):
            opts["output"] = parts[i + 1]
            i += 2
        elif part in ("-s", "--spec") and i + 1 < len(parts):
            opts["spec"] = parts[i + 1]
            i += 2
        elif part in ("-f", "--file") and i + 1 < len(parts):
            opts["file"] = parts[i + 1]
            i += 2
        elif part in ("-d", "--dir") and i + 1 < len(parts):
            opts["dir"] = parts[i + 1]
            i += 2
        elif part in ("-e", "--error") and i + 1 < len(parts):
            opts["error"] = parts[i + 1]
            i += 2
        elif part in ("-r", "--review") and i + 1 < len(parts):
            opts["review"] = parts[i + 1]
            i += 2
        elif part in ("-i", "--instruction") and i + 1 < len(parts):
            opts["instruction"] = parts[i + 1]
            i += 2
        elif part == "--focus" and i + 1 < len(parts):
            opts["focus"] = parts[i + 1]
            i += 2
        elif part in ("-c", "--command") and i + 1 < len(parts):
            opts["command"] = parts[i + 1]
            i += 2
        elif part in ("-m", "--max-iterations") and i + 1 < len(parts):
            opts["max_iterations"] = parts[i + 1]
            i += 2
        elif part in ("-y", "--yes"):
            opts["yes"] = "true"
            i += 1
        elif part in ("-b", "--branch") and i + 1 < len(parts):
            opts["branch"] = parts[i + 1]
            i += 2
        elif part in ("-t", "--title") and i + 1 < len(parts):
            opts["title"] = parts[i + 1]
            i += 2
        elif part == "--body" and i + 1 < len(parts):
            opts["body"] = parts[i + 1]
            i += 2
        elif part == "--interactive":
            opts["interactive"] = "true"
            i += 1
        elif part in ("-p", "--pipeline"):
            opts["pipeline"] = "true"
            i += 1
        elif part == "--draft":
            opts["draft"] = "true"
            i += 1
        elif part in ("-i", "--instruction") and i + 1 < len(parts):
            opts["instruction"] = parts[i + 1]
            i += 2
        elif part in ("-a", "--attempts") and i + 1 < len(parts):
            opts["attempts"] = parts[i + 1]
            i += 2
        elif part in ("-f", "--file") and i + 1 < len(parts):
            opts["file"] = parts[i + 1]
            i += 2
        elif part == "--model" and i + 1 < len(parts):
            opts["model"] = parts[i + 1]
            i += 2
        else:
            req_parts.append(part)
            i += 1
    return opts, " ".join(req_parts)


def show_repl_help(console: Console) -> None:
    """Print the interactive REPL slash command help list."""
    table = Table(
        title="[bold green]Zero Action CLI REPL Help[/bold green]",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Command", style="bold white")
    table.add_column("Description", style="dim")

    table.add_row("/help", "Show this help menu")
    table.add_row("/clear", "Clear the terminal screen")
    table.add_row("/init", "Scan workspace directory for repository context cache")
    table.add_row("/setup", "Interactive provider configuration wizard")
    table.add_row("/switch <provider> [model]", "Quickly switch active AI provider & model on the fly")
    table.add_row(
        "/provider [list/switch/test/models]",
        "View, configure, or test AI providers",
    )
    table.add_row("/plan [requirements]", "AI-generate Product Requirement Document (PRD)")
    table.add_row("/architect [requirements]", "AI-generate Architecture design document")
    table.add_row("/code [requirements]", "AI-generate project files with overwrite protection")
    table.add_row(
        "/review [file/dir]",
        "AI-perform code reviews (security, performance, maintainability...)",
    )
    table.add_row("/fix [file] [error/instruction]", "Surgically patch files with diff verification")
    table.add_row(
        "/memory [backup/restore/search/...]",
        "Manage chats, decisions, knowledge base, or backup/restore SQLite vector indexes",
    )
    table.add_row("/test [command]", "Run tests or checks and trigger autonomous self-healing")
    table.add_row("/pr [--prune]", "Automate Git commits/PRs, or clean merged local branches with --prune")
    table.add_row("/config [show/set]", "Display or assign app configurations dynamically")
    table.add_row("/tokens", "View summarized token usage and estimated API cost dashboard")
    table.add_row("/schema", "Scan workspace code structure and display DB models & REST routes tree")
    table.add_row("/refactor --file <file> --instruction <instruction>", "Agentic refactor target file, run quality checks, and auto-rollback on fail")
    table.add_row("/docker", "Docker Auto-Pilot: generate container configs, run, and self-heal start logs")
    table.add_row("/voice", "Voice Mode REPL Chat: record mic audio, transcribe, and run completions")
    table.add_row("/crawl <URL>", "Crawl documentation webpage recursively and import to knowledge base")
    table.add_row("/docmaker", "Scan project endpoints and generate markdown API documentation")
    table.add_row("/testgen <file>", "Automatically analyze a file and generate robust unit tests with pytest")
    table.add_row("/dashboard", "Launch the interactive Terminal User Interface (TUI) Dashboard")
    table.add_row("/benchmark [--model MODEL]", "Benchmark the latency, throughput, and cost of the active AI model")
    table.add_row("/mock [--port PORT] [stop]", "Scan project endpoints and spin up a mock API server in background")
    table.add_row("/release [--version VERSION]", "Analyze git history and generate release notes & CHANGELOG.md")
    table.add_row("/shortcut [add/remove/list]", "Manage shell aliases and shortcuts (e.g. zask for zero ask)")
    table.add_row("/devcontainer", "Detect project tech stack and generate VS Code dev container files")
    table.add_row("/verify", "Run all self-verification checks (pytest, ruff, mypy) autonomously")
    table.add_row("/exit / /quit", "Quit the interactive loop")

    console.print(table)


def handle_provider_command(parts: list[str], cmd_args: str, ctx: typer.Context, console: Console) -> None:
    """Dispatch provider subcommands."""
    from zero.cli.commands.provider import (
        default_callback as provider_show,
        list_providers,
        add_provider,
        remove_provider,
        switch_provider,
        list_models as provider_models,
        test_provider,
    )
    if len(parts) == 1:
        provider_show(ctx)
    else:
        sub = parts[1].lower()
        if sub == "list":
            list_providers(ctx)
        elif sub == "add" and len(parts) > 2:
            add_provider(ctx, parts[2])
        elif sub == "remove" and len(parts) > 2:
            remove_provider(ctx, parts[2])
        elif sub == "switch" and len(parts) > 2:
            switch_provider(ctx, parts[2])
        elif sub == "models":
            prov = parts[2] if len(parts) > 2 else None
            provider_models(ctx, prov)
        elif sub == "test":
            prov = parts[2] if len(parts) > 2 else None
            test_provider(ctx, prov)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown provider subcommand: '{sub}'.")


def handle_memory_command(parts: list[str], cmd_args: str, ctx: typer.Context, console: Console) -> None:
    """Dispatch memory subcommands."""
    from zero.cli.commands.memory import (
        list_sessions,
        show_session,
        delete_session,
        add_decision,
        list_decisions,
        import_knowledge,
        search as memory_search,
        memory_backup,
        memory_restore,
    )
    if len(parts) < 2:
        console.print("[bold red]Error:[/bold red] Missing memory subcommand (e.g. /memory list-decisions).")
        return
    sub = parts[1].lower()
    if sub == "list-sessions":
        list_sessions(ctx)
    elif sub == "show-session" and len(parts) > 2:
        show_session(ctx, parts[2])
    elif sub == "delete-session" and len(parts) > 2:
        delete_session(ctx, parts[2])
    elif sub == "add-decision":
        content = " ".join(parts[2:])
        add_decision(ctx, content)
    elif sub == "list-decisions":
        list_decisions(ctx)
    elif sub == "import-knowledge" and len(parts) > 2:
        import_knowledge(ctx, Path(parts[2]))
    elif sub == "search" and len(parts) > 2:
        query_val = " ".join(parts[2:])
        memory_search(ctx, query_val)
    elif sub == "backup":
        output_val = parts[2] if len(parts) > 2 else None
        memory_backup(ctx, output=output_val)
    elif sub == "restore" and len(parts) > 2:
        memory_restore(ctx, Path(parts[2]))
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown memory subcommand: '{sub}'.")


def handle_config_command(parts: list[str], cmd_args: str, ctx: typer.Context, console: Console) -> None:
    """Dispatch config subcommands."""
    from zero.cli.commands.config import show as config_show, set_value as config_set
    if len(parts) < 2:
        console.print("[bold red]Error:[/bold red] Missing config subcommand (e.g. /config show).")
        return
    sub = parts[1].lower()
    if sub == "show":
        config_show(ctx)
    elif sub == "set" and len(parts) > 3:
        config_set(ctx, parts[2], parts[3])
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown config subcommand: '{sub}'.")



def handle_slash_command(
    user_input: str,
    ctx: typer.Context,
    console: Console,
    session_id: Optional[str] = None,
    memory: Optional[MemoryManager] = None,
) -> bool:
    """Handle slash commands inside REPL. Returns True if REPL loop should exit."""
    try:
        parts = shlex.split(user_input)
    except Exception:
        parts = user_input.split()

    if not parts:
        return False

    cmd = parts[0].lower()
    cmd_args = user_input[len(cmd):].strip()

    if cmd in ("/exit", "/quit"):
        console.print("[green]Chat REPL session closed. Goodbye![/green]")
        return True

    if cmd == "/clear":
        console.clear()
        return False

    if cmd == "/help":
        show_repl_help(console)
        return False

    try:
        if cmd == "/init":
            from zero.cli.commands.init import init
            init(ctx)

        elif cmd == "/setup":
            from zero.cli.commands.setup import setup
            setup(ctx)

        elif cmd == "/provider":
            handle_provider_command(parts, cmd_args, ctx, console)

        elif cmd == "/plan":
            from zero.cli.commands.plan import plan
            opts, reqs = parse_slash_args(cmd_args)
            out_path = Path(opts["output"]) if "output" in opts else Path("docs/prd.md")
            plan(ctx, requirements=reqs if reqs else "", output=out_path)

        elif cmd == "/architect":
            from zero.cli.commands.architect import architect
            opts, reqs = parse_slash_args(cmd_args)
            out_path = Path(opts["output"]) if "output" in opts else Path("docs/architecture.md")
            architect(ctx, requirements=reqs if reqs else "", output=out_path)

        elif cmd == "/code":
            from zero.cli.commands.code import code
            opts, reqs = parse_slash_args(cmd_args)
            code_out_path: Optional[Path] = Path(opts["output"]) if "output" in opts else None
            spec_path: Optional[Path] = Path(opts["spec"]) if "spec" in opts else None
            code(ctx, requirements=reqs if reqs else "", output=cast(Any, code_out_path), spec=cast(Any, spec_path))

        elif cmd == "/review":
            from zero.cli.commands.review import review
            opts, reqs = parse_slash_args(cmd_args)
            file_val: Optional[Path] = None
            dir_val: Optional[Path] = None
            if reqs:
                target = Path(reqs.split()[0])
                if target.is_file():
                    file_val = target
                elif target.is_dir():
                    dir_val = target

            review_file: Optional[Path] = Path(opts["file"]) if "file" in opts else file_val
            review_dir: Optional[Path] = Path(opts["dir"]) if "dir" in opts else dir_val
            review_out_path: Optional[Path] = Path(opts["output"]) if "output" in opts else None
            focus_val = opts.get("focus", "security,performance,maintainability,scalability,readability")
            model_val = opts.get("model")

            review(
                ctx,
                file=cast(Any, review_file),
                dir=cast(Any, review_dir),
                output=cast(Any, review_out_path),
                focus=focus_val,
                model=model_val
            )

        elif cmd == "/fix":
            from zero.cli.commands.fix import fix
            opts, reqs = parse_slash_args(cmd_args)
            req_list = reqs.split() if reqs else []

            fix_file_val: Optional[Path] = Path(opts["file"]) if "file" in opts else (Path(req_list[0]) if req_list else None)
            instr_val = opts.get("instruction") or (" ".join(req_list[1:]) if len(req_list) > 1 else None)
            review_val: Optional[Path] = Path(opts["review"]) if "review" in opts else None
            fix_out_path: Optional[Path] = Path(opts["output"]) if "output" in opts else None
            err_val = opts.get("error")
            interactive_val = opts.get("interactive") == "true"

            fix(
                ctx,
                file=cast(Any, fix_file_val),
                error=err_val,
                review_report=cast(Any, review_val),
                instruction=instr_val,
                output=cast(Any, fix_out_path),
                interactive=interactive_val
            )

        elif cmd == "/test":
            from zero.cli.commands.test import test
            opts, reqs = parse_slash_args(cmd_args)
            test_cmd = opts.get("command") or reqs or "pytest"
            try:
                max_iters = int(opts.get("max_iterations") or 3)
            except ValueError:
                max_iters = 3
            file_val = Path(opts["file"]) if "file" in opts else None
            yes_val = opts.get("yes") == "true"
            pipeline_val = opts.get("pipeline") == "true"
            test(ctx, command=test_cmd, max_iterations=max_iters, file=file_val, yes=yes_val, pipeline=pipeline_val)

        elif cmd == "/pr":
            from zero.cli.commands.pr import pr
            opts, reqs = parse_slash_args(cmd_args)
            branch_val = opts.get("branch")
            title_val = opts.get("title")
            body_val = opts.get("body")
            yes_val = opts.get("yes") == "true"
            draft_val = opts.get("draft") == "true"
            prune_val = opts.get("prune") == "true" or "prune" in reqs.lower()
            pr(ctx, branch=branch_val, title=title_val, body=body_val, yes=yes_val, push=True, draft=draft_val, prune=prune_val)

        elif cmd == "/refactor":
            from zero.cli.commands.refactor import refactor as run_refactor
            opts, reqs = parse_slash_args(cmd_args)
            file_val = Path(opts["file"]) if "file" in opts else None
            instr_val = opts.get("instruction") or reqs or ""
            try:
                attempts_val = int(opts.get("attempts") or 2)
            except ValueError:
                attempts_val = 2
            
            if not file_val or not instr_val:
                console.print("[bold red]Error:[/bold red] Missing --file or --instruction parameters.")
            else:
                run_refactor(ctx, file=file_val, instruction=instr_val, max_attempts=attempts_val)

        elif cmd == "/memory":
            handle_memory_command(parts, cmd_args, ctx, console)

        elif cmd == "/config":
            handle_config_command(parts, cmd_args, ctx, console)

        elif cmd == "/search":
            from zero.cli.commands.search import search
            query_val = cmd_args.strip()
            if not query_val:
                console.print("[bold red]Error:[/bold red] Missing search query.")
            else:
                search(ctx, query_val)
                if memory and session_id:
                    from zero.services.search import search_ddg
                    results = search_ddg(query_val)
                    if results and results[0]["title"] != "Error":
                        summary = "\n".join(f"- Title: {r['title']}\n  URL: {r['url']}\n  Snippet: {r['snippet']}" for r in results[:3])
                        msg_text = f"[System Search Note] Web search results for '{query_val}':\n{summary}"
                        try:
                            memory.sessions.add_message(
                                message_id=str(uuid.uuid4())[:8],
                                session_id=session_id,
                                role="system",
                                content=msg_text,
                                token_count=0
                            )
                            console.print("[dim green](Search results injected into chat memory)[/dim green]")
                        except Exception as e:
                            logger.bind(category="cli").debug(f"Failed to inject search results to session: {e}")

        elif cmd == "/switch":
            args_parts = cmd_args.strip().split(maxsplit=1)
            if not args_parts:
                console.print(
                    "[bold red]Error:[/bold red] Missing provider name. "
                    "Usage: /switch <provider> [model]"
                )
            else:
                new_provider = args_parts[0].lower()
                from zero.providers.registry import PROVIDER_CLASSES
                if new_provider not in PROVIDER_CLASSES:
                    console.print(
                        f"[bold red]Error:[/bold red] Unsupported provider '{new_provider}'. "
                        f"Available options: {list(PROVIDER_CLASSES.keys())}"
                    )
                else:
                    new_model = args_parts[1] if len(args_parts) > 1 else None
                    ctx.obj.settings.provider.active_provider = new_provider
                    if new_model:
                        provider_settings = getattr(ctx.obj.settings.provider, new_provider)
                        provider_settings.model = new_model
                    
                    from zero.services.config import save_config
                    save_config(ctx.obj.settings, ctx.obj.config_dir)
                    
                    console.print(
                        f"[bold green]✓ Switched active provider to [cyan]{new_provider}[/cyan]"
                        + (f" with model [white]{new_model}[/white]" if new_model else "")
                        + "[/bold green]"
                    )

        elif cmd == "/read":
            from zero.cli.commands.search import read
            url_val = cmd_args.strip()
            if not url_val:
                console.print("[bold red]Error:[/bold red] Missing webpage URL.")
            else:
                read(ctx, url_val)
                if memory and session_id:
                    from zero.services.search import fetch_url_text
                    text = fetch_url_text(url_val)
                    if not text.startswith("Error reading URL"):
                        msg_text = f"[System Doc Note] Webpage content from {url_val}:\n{text}"
                        try:
                            memory.sessions.add_message(
                                message_id=str(uuid.uuid4())[:8],
                                session_id=session_id,
                                role="system",
                                content=msg_text,
                                token_count=0
                            )
                        except Exception as e:
                            logger.bind(category="cli").debug(f"Failed to inject page text to session: {e}")

        elif cmd == "/learn":
            rule_text = cmd_args.strip()
            if not rule_text:
                console.print("[bold red]Error:[/bold red] Missing rule text (e.g. /learn 'always use UTF-8').")
            else:
                try:
                    if not memory:
                        raise ValueError("Memory subsystem is not initialized. Run 'zero init' first.")
                    rule_id = f"rule_{uuid.uuid4().hex[:8]}"
                    project_path = str(Path.cwd().resolve())
                    memory.decisions.add_decision(
                        decision_id=rule_id,
                        project_path=project_path,
                        title="Learned Rule",
                        problem="Persistent project rule",
                        solution=rule_text,
                        status="learned"
                    )
                    console.print("[bold green]Success: Rule learned and persisted to project memory.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Error saving rule:[/bold red] {e}")

        elif cmd == "/tokens":
            from zero.cli.commands.billing import billing
            billing(ctx)

        elif cmd == "/crawl":
            url_val = cmd_args.strip()
            if not url_val:
                console.print("[bold red]Error:[/bold red] Missing crawler target URL.")
            else:
                try:
                    from zero.services.search import fetch_url_text, _urlopen_safe
                    import urllib.parse
                    import urllib.request
                    import re
                    
                    console.print(f"[yellow]Starting crawler on: {url_val}...[/yellow]")
                    parsed_root = urllib.parse.urlparse(url_val)
                    domain = parsed_root.netloc
                    prefix = parsed_root.path
                    
                    main_html = ""
                    req = urllib.request.Request(
                        url_val,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/120.0.0.0 Safari/537.36"
                            )
                        }
                    )
                    with _urlopen_safe(req, timeout=8) as resp:
                        main_html = resp.read().decode("utf-8", errors="replace")
                        
                    links_found = re.findall(r'href=["\']([^"\']+)["\']', main_html)
                    urls_to_crawl = [url_val]
                    for link in links_found:
                        full_url = urllib.parse.urljoin(url_val, link)
                        parsed_link = urllib.parse.urlparse(full_url)
                        if parsed_link.netloc == domain and parsed_link.path.startswith(prefix):
                            clean_url = urllib.parse.urlunparse((parsed_link.scheme, parsed_link.netloc, parsed_link.path, "", "", ""))
                            if clean_url not in urls_to_crawl:
                                urls_to_crawl.append(clean_url)
                                
                    urls_to_crawl = urls_to_crawl[:10]
                    console.print(f"[cyan]Found {len(urls_to_crawl)} matching pages to crawl.[/cyan]")
                    
                    crawled_count = 0
                    for page_url in urls_to_crawl:
                        console.print(f"Reading: [dim]{page_url}[/dim]...")
                        page_text = fetch_url_text(page_url)
                        if page_text and not page_text.startswith("Error reading URL"):
                            if not memory:
                                raise ValueError("Memory subsystem is not initialized. Run 'zero init' first.")
                            knowledge_id = f"crawl_{uuid.uuid4().hex[:8]}"
                            page_title = page_url.split("/")[-1] or page_url.split("/")[-2] or "Crawled Doc"
                            memory.knowledge.add_knowledge(
                                knowledge_id=knowledge_id,
                                title=page_title,
                                content=page_text,
                                source=page_url
                            )
                            crawled_count += 1
                            
                    console.print(f"[bold green]Success: Crawled and indexed {crawled_count} pages into knowledge base.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Crawler error:[/bold red] {e}")

        elif cmd == "/schema":
            from zero.cli.commands.schema import schema as run_schema
            run_schema(ctx)

        elif cmd == "/docker":
            from zero.cli.commands.docker import docker as run_docker
            run_docker(ctx)

        elif cmd == "/voice":
            from zero.services.ai import AIService
            config_dir = ctx.obj.config_dir
            ai_service = AIService(ctx.obj.settings, config_dir)
            provider = ai_service.get_provider()
            
            def _speak_text_offline(text: str) -> None:
                """Speak text out loud using native, free, offline OS speech engines."""
                import sys
                import subprocess
                import shutil
                cleaned = "".join(c for c in text if c.isalnum() or c in " .,!?-")
                if not cleaned.strip():
                    return
                try:
                    if sys.platform == "win32":
                        # Windows SAPI SpVoice
                        cmd_str = f"(New-Object -ComObject SAPI.SpVoice).Speak('{cleaned}')"
                        subprocess.run(["powershell", "-Command", cmd_str], capture_output=True, timeout=15)
                    elif sys.platform == "darwin":
                        subprocess.run(["say", cleaned], capture_output=True, timeout=15)
                    else:
                        if shutil.which("spd-say"):
                            subprocess.run(["spd-say", cleaned], capture_output=True, timeout=15)
                        elif shutil.which("espeak"):
                            subprocess.run(["espeak", cleaned], capture_output=True, timeout=15)
                except Exception:
                    pass

            def _transcribe_audio(file_p: Path) -> str:
                """Transcribe audio using local offline Whisper if available, falling back to OpenAI Whisper API."""
                try:
                    import whisper
                    console.print("[yellow]Using local offline Whisper model...[/yellow]")
                    model = whisper.load_model("base")
                    result = model.transcribe(str(file_p))
                    return result.get("text", "")
                except Exception as e_local:
                    console.print(f"[dim yellow]Local Whisper failed ({e_local}). Falling back to API...[/dim yellow]")
                    pass
                
                openai_api_key = None
                try:
                    openai_provider = ai_service.provider_manager.get_provider("openai")
                    op_key = getattr(openai_provider, "api_key", None)
                    if op_key and not op_key.startswith("sk-1234"):
                        openai_api_key = op_key
                except Exception:
                    pass

                if not openai_api_key:
                    if ctx.obj.settings.provider.active_provider.lower() == "openai":
                        openai_api_key = getattr(provider, "api_key", None)

                if not openai_api_key:
                    raise ValueError(
                        "The active provider (OpenRouter) does not support audio transcription. "
                        "Please configure a valid OpenAI API key under 'provider.openai' in your providers.toml, "
                        "or install the local offline Whisper engine using 'pip install openai-whisper'."
                    )

                import litellm
                with open(file_p, "rb") as audio_file:
                    resp = litellm.transcription(
                        model="whisper-1",
                        file=audio_file,
                        api_key=openai_api_key
                    )
                return resp.get("text", "")

            try:
                import sounddevice as sd
                import soundfile as sf
                
                duration = 5
                fs = 16000
                console.print(f"[yellow]🎙️ Recording voice for {duration} seconds... Speak now![/yellow]")
                myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                console.print("[green]✓ Recording finished.[/green]")
                
                audio_path = config_dir / "temp_voice.wav"
                sf.write(str(audio_path), myrecording, fs)
                
                console.print("[yellow]Transcribing audio utilizing Whisper...[/yellow]")
                
                query_text = _transcribe_audio(audio_path)
                console.print(f"[bold cyan]You said:[/bold cyan] {query_text}")
                
                if query_text:
                    console.print(f"[yellow]Sending query to active model {provider.model}...[/yellow]")
                    messages = [{"role": "user", "content": query_text}]
                    response_text = asyncio.run(stream_completion_with_timer(provider, messages, console))
                    
                    try:
                        console.print("[dim green]Synthesizing local offline voice speech...[/dim green]")
                        _speak_text_offline(response_text)
                    except Exception as e_tts:
                        logger.bind(category="cli").debug(f"Local TTS failed: {e_tts}")
            except ImportError:
                console.print("[bold red]Voice Mode Requirements Missing:[/bold red]")
                console.print("[yellow]To enable recording directly from terminal, run:[/yellow]")
                console.print("[bold white]uv pip install sounddevice soundfile numpy[/bold white]")
                console.print("\n[yellow]Alternative: Simulated Voice Mode[/yellow]")
                voice_file_path = Prompt.ask("Enter the path to a pre-recorded WAV/MP3 audio file to parse")
                if voice_file_path and Path(voice_file_path).exists():
                    try:
                        query_text = _transcribe_audio(Path(voice_file_path))
                        console.print(f"[bold cyan]Transcribed text:[/bold cyan] {query_text}")
                        if query_text:
                            messages = [{"role": "user", "content": query_text}]
                            response_text = asyncio.run(stream_completion_with_timer(provider, messages, console))
                            try:
                                _speak_text_offline(response_text)
                            except Exception:
                                pass
                    except Exception as e_trans:
                        console.print(f"[bold red]Transcription failed:[/bold red] {e_trans}")
                else:
                    console.print("[red]File not found or empty path. Voice mode aborted.[/red]")
            except Exception as e:
                console.print(f"[bold red]Voice Mode error:[/bold red] {e}")

        elif cmd == "/docmaker":
            from zero.cli.commands.doc_gen import doc_gen as run_doc_gen
            run_doc_gen(ctx)

        elif cmd == "/testgen":
            from zero.cli.commands.test_gen import run_test_gen
            opts, reqs = parse_slash_args(cmd_args)
            file_val = Path(opts["file"]) if "file" in opts else (Path(reqs.split()[0]) if reqs else None)
            if not file_val:
                console.print("[bold red]Error:[/bold red] Please specify the target file (e.g. /testgen my_file.py).")
            else:
                run_test_gen(ctx, file=file_val)

        elif cmd == "/dashboard":
            from zero.cli.commands.dashboard import dashboard as run_dashboard
            run_dashboard(ctx)

        elif cmd == "/benchmark":
            from zero.cli.commands.benchmark import run_benchmark, DEFAULT_BENCHMARK_PROMPT
            opts, reqs = parse_slash_args(cmd_args)
            model_val = opts.get("model")
            prompt_val = reqs if reqs else DEFAULT_BENCHMARK_PROMPT
            run_benchmark(ctx, model=model_val, prompt=prompt_val)

        elif cmd == "/mock":
            from zero.cli.commands.mock_server import mock_server
            opts, reqs = parse_slash_args(cmd_args)
            try:
                port_val = int(opts.get("port") or 8000)
            except ValueError:
                port_val = 8000
            stop_val = "stop" in reqs.lower() or "stop" in opts
            mock_server(ctx, port=port_val, background=True, stop=stop_val)

        elif cmd == "/release":
            from zero.cli.commands.release import generate_release_notes
            opts, reqs = parse_slash_args(cmd_args)
            version_val = opts.get("version") or (reqs if reqs else None)
            generate_release_notes(ctx, version=version_val)

        elif cmd == "/shortcut":
            from zero.cli.commands.shortcut import run_shortcut
            opts, reqs = parse_slash_args(cmd_args)
            action_val = reqs.split()[0] if reqs else "list"
            name_val = opts.get("name")
            command_val = opts.get("command")
            run_shortcut(ctx, action=action_val, name=name_val, command=command_val)

        elif cmd == "/devcontainer":
            from zero.cli.commands.devcontainer import generate_devcontainer
            generate_devcontainer(ctx)

        elif cmd == "/verify":
            console.print("[yellow]Running autonomous self-verification checks...[/yellow]\n")
            import subprocess
            
            # 1. Run Ruff
            console.print("Running [bold cyan]Ruff Style Linter[/bold cyan]...")
            ruff_res = subprocess.run(["uv", "run", "ruff", "check", "zero", "tests"], capture_output=True, text=True)
            ruff_ok = ruff_res.returncode == 0
            
            # 2. Run Mypy
            console.print("Running [bold cyan]Mypy Static Type Checker[/bold cyan]...")
            mypy_res = subprocess.run(["uv", "run", "mypy", "zero", "tests", "--ignore-missing-imports"], capture_output=True, text=True)
            mypy_ok = mypy_res.returncode == 0
            
            # 3. Run Pytest
            console.print("Running [bold cyan]Pytest Unit Test Suite[/bold cyan]...")
            pytest_res = subprocess.run(["uv", "run", "pytest"], capture_output=True, text=True)
            pytest_ok = pytest_res.returncode == 0
            
            # Output Results Table
            table = Table(title="[bold green]Workspace Verification Results[/bold green]", show_header=True, header_style="bold cyan")
            table.add_column("Check", style="bold white")
            table.add_column("Status", style="bold")
            table.add_column("Details", style="dim")
            
            table.add_row("Ruff Style & Formatting", "[green]PASS[/green]" if ruff_ok else "[red]FAIL[/red]", "Clean" if ruff_ok else ruff_res.stdout.splitlines()[0] if ruff_res.stdout else "Issues found")
            table.add_row("Mypy Type Safety", "[green]PASS[/green]" if mypy_ok else "[red]FAIL[/red]", "Type safe" if mypy_ok else mypy_res.stdout.splitlines()[-1] if mypy_res.stdout else "Issues found")
            table.add_row("Pytest Suite", "[green]PASS[/green]" if pytest_ok else "[red]FAIL[/red]", "All tests passed" if pytest_ok else "Some tests failed")
            
            console.print(table)

        else:
            console.print(
                f"[bold red]Error:[/bold red] Unknown slash command: '{cmd}'. "
                f"Type [bold cyan]/help[/bold cyan] for a list of commands."
            )

    except typer.Exit:
        pass
    except typer.Abort:
        console.print("\n[yellow]Command aborted.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Command error:[/bold red] {e}")

    return False


try:
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document
    from prompt_toolkit.styles import Style
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    class Completer:  # type: ignore[no-redef]
        pass
    class Document:  # type: ignore[no-redef]
        pass
    Completion = None  # type: ignore[assignment,misc]
    Style = None  # type: ignore[assignment,misc]
    PromptSession = None  # type: ignore[assignment,misc]
    HTML = None  # type: ignore[assignment,misc]
    HAS_PROMPT_TOOLKIT = False


class ZeroChatCompleter(Completer):
    """Dropdown autocompleter displaying description metadata for zero slash commands."""

    def __init__(self, commands_with_meta: Dict[str, str], providers: List[str], settings: Any) -> None:
        self.commands_with_meta = commands_with_meta
        self.providers = providers
        self.settings = settings
        # Model pool: (model_id, display_name, provider_name, cost_status)
        self.models_pool = [
            ("mimo-v2.5-free", "MiMo V2.5 Free", "OpenCode Zen", "Free"),
            ("nemotron-3-ultra-free", "Nemotron 3 Ultra Free", "OpenCode Zen", "Free"),
            ("deepseek-v4-flash-free", "DeepSeek V4 Flash Free", "OpenCode Zen", "Free"),
            ("north-mini-code-free", "North Mini Code Free", "OpenCode Zen", "Free"),
            ("gpt-4o", "GPT-4o", "OpenAI", "Paid"),
            ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet", "Anthropic", "Paid"),
            ("gemini-1.5-pro", "Gemini 1.5 Pro", "Gemini", "Paid"),
            ("openrouter/meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "OpenRouter", "Paid"),
        ]

    def get_completions(self, document: Document, complete_event: Any):
        text = document.text_before_cursor
        words = text.split()
        
        # Check if they are typing switch command models list
        if text.startswith("/switch"):
            query = text.replace("/switch", "").strip().lower()
            for model_id, model_name, provider_name, status in self.models_pool:
                provider_key = provider_name.lower().replace(" ", "_")
                replacement = f"/switch {provider_key} {model_id}"
                
                # Format to fixed columns matching user mockup
                display_str = f"{model_name:<30} {provider_name:<20} {status:>10}"
                
                # Show all if empty query, or match search term against display strings
                if not query or query in model_name.lower() or query in provider_name.lower() or query in status.lower() or query in model_id.lower():
                    yield Completion(
                        replacement,
                        start_position=-len(text),
                        display=display_str
                    )
            return

        if text.startswith("/"):
            if len(words) == 0 or (len(words) == 1 and not text.endswith(" ")):
                target = words[0] if words else "/"
                for cmd, desc in self.commands_with_meta.items():
                    if cmd.startswith(target):
                        yield Completion(
                            cmd,
                            start_position=-len(target),
                            display=cmd,
                            display_meta=desc
                        )
                return


def chat(ctx: typer.Context) -> None:
    """Start an interactive chat session with context and memory tracking."""
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

    db_path = config_dir / "memory.db"
    memory = MemoryManager(db_path)
    session_id = str(uuid.uuid4())[:8]
    session_title = f"Chat Session {session_id}"

    try:
        memory.sessions.create_session(session_id, session_title)
    except Exception as e:
        logger.bind(category="cli").error(f"Failed to initialize chat session in database: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not initialize session memory: {e}")
        raise typer.Exit(code=1)

    active_provider = settings.provider.active_provider or "none"
    provider_defaults = getattr(settings.provider, active_provider) if active_provider != "none" else None
    active_model = provider_defaults.model if provider_defaults else "none"
    cwd_name = Path.cwd().name

    # Render premium startup welcome screen matching Claude Code CLI layout
    welcome_panel = Panel(
        Text(" Welcome To The Zero Action ", style="bold #FFD700"),
        border_style="#FFD700",
        expand=False,
    )
    console.print(welcome_panel)

    try:
        from zero.cli.commands.logo_data import LOGO_MARKUP
        for line in LOGO_MARKUP:
            console.print(line)
    except Exception:
        console.print("[bold red]  ZERO ACTION[/bold red]")

    try:
        Prompt.ask("\n🎉 [bold #5fafff]Connection successful. Press[/bold #5fafff] [bold white]Enter[/bold white] [bold #5fafff]to continue[/bold #5fafff]", default="", show_default=False)
    except (KeyboardInterrupt, EOFError, typer.Abort):
        console.print("\n[yellow]REPL session terminated.[/yellow]")
        raise typer.Exit()

    import sys
    use_prompt_toolkit = HAS_PROMPT_TOOLKIT
    if os.environ.get("ZERO_TESTING") == "true" or not sys.stdout.isatty():
        use_prompt_toolkit = False


    session: Any = None
    if use_prompt_toolkit:
        try:
            from zero.cli.commands.chat_tui import run_tui
            run_tui(ctx, settings, config_dir, ai_service, memory, session_id)
            return
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to initialize TUI: {e}")
            use_prompt_toolkit = False

    # Clear console screen for interactive prompt
    console.clear()

    console.print(
        Panel(
            f"Active Provider: [bold cyan]{active_provider}[/bold cyan] | "
            f"Model: [bold cyan]{active_model}[/bold cyan]\n"
            f"Workspace Directory: [white]{Path.cwd()}[/white]\n"
            f"Session ID: [cyan]{session_id}[/cyan]\n\n"
            f"Type [bold green]/help[/bold green] to list commands. "
            f"Type [bold green]/exit[/bold green] or [bold green]/quit[/bold green] to end the session.",
            title="[bold green]Zero Action Chat Console[/bold green]",
            border_style="green",
        )
    )

    if not use_prompt_toolkit:
        console.print("[dim yellow]💡 Tip: Run 'pip install prompt-toolkit' to enable premium interactive dropdown autocomplete menus for commands and models.[/dim yellow]\n")


    while True:
        try:
            # Dynamically refresh provider configuration on each loop iteration
            active_provider = settings.provider.active_provider or "none"
            provider_defaults = getattr(settings.provider, active_provider) if active_provider != "none" else None
            active_model = provider_defaults.model if provider_defaults else "none"
            try:
                provider = ai_service.get_provider()
            except Exception:
                pass

            # Build Claude Code styled prompt for fallback
            prompt_str = (
                f"[bold green]zero-action[/bold green] "
                rf"\[[cyan]{active_provider}/{active_model}[/cyan]\] "
                f"[blue]{cwd_name}[/blue] >"
            )

            if use_prompt_toolkit and session:
                prompt_html = (
                    f"<green><b>zero-action</b></green> "
                    rf"\[<cyan>{active_provider}/{active_model}</cyan>\] "
                    f"<blue>{cwd_name}</blue> &gt; "
                )
                try:
                    user_input = session.prompt(HTML(prompt_html))
                except Exception:
                    user_input = Prompt.ask(prompt_str)
            else:
                user_input = Prompt.ask(prompt_str)
        except (KeyboardInterrupt, EOFError, typer.Abort):
            console.print("\n[yellow]REPL session terminated.[/yellow]")
            break

        if not user_input.strip():
            continue

        # Check for slash commands
        if user_input.strip().startswith("/"):
            should_exit = handle_slash_command(
                user_input.strip(),
                ctx,
                console,
                session_id=session_id,
                memory=memory,
            )
            if should_exit:
                break
            continue

        # Standard conversation path
        user_msg_id = str(uuid.uuid4())[:8]
        try:
            memory.sessions.add_message(
                message_id=user_msg_id,
                session_id=session_id,
                role="user",
                content=user_input,
                token_count=provider.token_count(user_input),
            )
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to save user message: {e}")

        history = memory.sessions.get_messages(session_id)
        system_prompt = ai_service.get_system_prompt(Path.cwd(), query=user_input)

        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        console.print("\n[bold green]Zero Action Assistant:[/bold green]")

        try:
            assistant_response = asyncio.run(stream_completion_with_timer(provider, api_messages, console))

        except Exception as e:
            logger.bind(category="cli").error(f"Error during streaming chat completion: {e}")
            console.print(f"\n[bold red]API Completion Error:[/bold red] {e}")
            break

        assistant_msg_id = str(uuid.uuid4())[:8]
        try:
            memory.sessions.add_message(
                message_id=assistant_msg_id,
                session_id=session_id,
                role="assistant",
                content=assistant_response,
                token_count=provider.token_count(assistant_response),
            )
        except Exception as e:
            logger.bind(category="cli").error(f"Failed to save assistant message: {e}")

        console.print()
