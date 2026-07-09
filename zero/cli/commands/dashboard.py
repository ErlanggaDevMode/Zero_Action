"""CLI subcommand for the interactive full-screen TUI status dashboard."""

import asyncio
import time
import subprocess
from typing import Any
import typer
from prompt_toolkit.application import Application
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Frame
from prompt_toolkit.key_binding import KeyBindings

from zero.services.billing import get_billing_summary
from zero.memory.manager import MemoryManager

dashboard_style = Style.from_dict({
    "line": "fg:#333333",
    "header": "fg:#5fafff bold",
    "text": "fg:#ffffff",
    "success": "fg:#5fff5f bold",
    "error": "fg:#ff5f5f bold",
    "warning": "fg:#ffaa00 bold",
    "info": "fg:#00ffff bold",
    "accent": "fg:#E07A5F bold",
    "frame.border": "fg:#333333",
    "frame.label": "fg:#ffffff bold",
    "status-bar": "bg:#111111 fg:#888888",
})

def dashboard(ctx: typer.Context) -> None:
    """Launch the interactive Terminal User Interface (TUI) Dashboard."""
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # 1. Resolve Active configurations
    active_provider = settings.provider.active_provider or "none"
    provider_defaults = getattr(settings.provider, active_provider) if active_provider != "none" else None
    active_model = provider_defaults.model if provider_defaults else "none"

    # SQLite Database connection
    db_path = config_dir / "memory.db"
    memory = MemoryManager(db_path)

    # Dashboard Live state
    state = {
        "git_status": "Checking...",
        "test_results": "Press [T] to execute pytest live",
        "last_updated": time.strftime("%H:%M:%S"),
        "total_sessions": 0,
        "total_messages": 0,
        "total_decisions": 0,
        "total_knowledge": 0,
        "total_calls": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
    }

    def refresh_data() -> None:
        state["last_updated"] = time.strftime("%H:%M:%S")

        # 1. Billing Info
        billing_summary = get_billing_summary()
        state["total_calls"] = billing_summary.get("total_calls", 0)
        state["total_tokens"] = billing_summary.get("total_prompt_tokens", 0) + billing_summary.get("total_completion_tokens", 0)
        state["total_cost"] = billing_summary.get("total_cost", 0.0)

        # 2. Git Status
        try:
            res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
            state["git_status"] = res.stdout.strip() or "✓ Working tree clean (no modified files)"
        except Exception as e:
            state["git_status"] = f"Error running git: {e}"

        # 3. SQLite Database statistics
        try:
            with memory.db.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM sessions")
                state["total_sessions"] = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM messages")
                state["total_messages"] = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM decisions")
                state["total_decisions"] = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM knowledge")
                state["total_knowledge"] = c.fetchone()[0]
        except Exception:
            pass

    # Initial Load
    refresh_data()

    # Layout Components
    def get_left_panel_content() -> HTML:
        return HTML(
            f" <b>PROVIDER CONFIGURATION</b>\n"
            f"  Active Provider : <accent>{active_provider}</accent>\n"
            f"  Model Name      : <text>{active_model}</text>\n\n"
            f" <b>BILLING & COST SUMMARY</b>\n"
            f"  Total API Calls : <info>{state['total_calls']}</info>\n"
            f"  Tokens Consumed : <info>{state['total_tokens']:,}</info>\n"
            f"  Estimated Cost  : <success>${state['total_cost']:.6f} USD</success>\n\n"
            f" <b>SEMANTIC MEMORY STORAGE</b>\n"
            f"  Database Path   : <text>{db_path.name}</text>\n"
            f"  Sessions Cached : <info>{state['total_sessions']}</info>\n"
            f"  Message Logs    : <info>{state['total_messages']}</info>\n"
            f"  Decision Rules  : <info>{state['total_decisions']}</info>\n"
            f"  RAG Docs Ingest : <info>{state['total_knowledge']}</info>\n"
        )

    def get_right_panel_content() -> HTML:
        # Wrap git status to avoid layout breaking
        git_lines = []
        git_status_str = str(state["git_status"])
        for line in git_status_str.splitlines()[:15]:
            if len(line) > 50:
                line = line[:47] + "..."
            git_lines.append(f"  {line}")
        git_fmt = "\n".join(git_lines)

        # Highlight test result colors
        test_res_str = str(state["test_results"])
        if "passed in" in test_res_str or "✓" in test_res_str:
            test_res_fmt = f"<success>{test_res_str}</success>"
        elif "failed in" in test_res_str or "✗" in test_res_str:
            test_res_fmt = f"<error>{test_res_str}</error>"
        else:
            test_res_fmt = f"<warning>{test_res_str}</warning>"

        return HTML(
            f" <b>LOCAL GIT CHANGES</b>\n"
            f"{git_fmt}\n\n"
            f" <b>LIVE QUALITY PIPELINE (PYTEST)</b>\n"
            f"  Test Runner Status:\n"
            f"  {test_res_fmt}\n"
        )

    def get_header_content() -> HTML:
        return HTML(
            " <header>Zero Action interactive CLI TUI Dashboard</header>"
        )

    def get_footer_content() -> HTML:
        return HTML(
            f"  [Q] Quit  •  [R] Refresh Info  •  [T] Run Pytest live  |  Last update: {state['last_updated']}"
        )

    root_container = HSplit([
        # Header title
        Frame(
            body=Window(content=FormattedTextControl(get_header_content), height=1),
            style="class:frame"
        ),
        
        # Split left and right panels
        VSplit([
            Frame(
                body=Window(content=FormattedTextControl(get_left_panel_content)),
                title="System Status",
                style="class:frame"
            ),
            Window(width=1, char="│", style="class:line"),
            Frame(
                body=Window(content=FormattedTextControl(get_right_panel_content)),
                title="Repository Status",
                style="class:frame"
            )
        ]),

        # Footer commands/status bar
        Window(content=FormattedTextControl(get_footer_content), height=1, style="class:status-bar")
    ])

    kb = KeyBindings()

    @kb.add("q")
    @kb.add("c-c")
    @kb.add("c-d")
    def _quit(event: Any) -> None:
        event.app.exit()

    @kb.add("r")
    def _refresh(event: Any) -> None:
        refresh_data()
        event.app.invalidate()

    @kb.add("t")
    def _run_tests(event: Any) -> None:
        state["test_results"] = "Running pytest... please wait"
        event.app.invalidate()

        async def _run() -> None:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "uv", "run", "pytest",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                out = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
                
                # Extract summary line from pytest output
                summary_line = ""
                for line in reversed(out.splitlines()):
                    if " passed in " in line or " failed in " in line or " error in " in line:
                        summary_line = line.strip()
                        break
                
                if not summary_line:
                    summary_line = "No tests output found"

                # Strip decoration color markers if pytest outputs them
                import re
                summary_line = re.sub(r'\x1b\[[0-9;]*m', '', summary_line)

                if proc.returncode == 0:
                    state["test_results"] = f"✓ {summary_line}"
                else:
                    state["test_results"] = f"✗ {summary_line}"
            except Exception as e:
                state["test_results"] = f"Error running tests: {e}"
            
            refresh_data()
            app.invalidate()

        asyncio.create_task(_run())

    app: Application = Application(
        layout=Layout(root_container),
        key_bindings=kb,
        style=dashboard_style,
        full_screen=True,
    )

    app.run()
