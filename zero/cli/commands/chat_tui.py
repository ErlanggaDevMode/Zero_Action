"""Full-screen interactive TUI chat console using prompt_toolkit."""

import asyncio
import time
import uuid
from pathlib import Path
from typing import Any, List

from prompt_toolkit.application import Application
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign, DynamicContainer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Frame, TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.data_structures import Point

from zero.services.billing import get_billing_summary
from zero.cli.commands.chat import ZeroChatCompleter

# Define theme colors matching the mockup layout
tui_style = Style.from_dict({
    "line": "fg:#333333",
    "user-header": "fg:#ffffff bold",
    "user-text": "fg:#e0e0e0",
    "thought": "fg:#ffa500 italic",
    "assistant-header": "fg:#5fafff bold",
    "assistant-text": "fg:#ffffff",
    "system-text": "fg:#888888",
    "success": "fg:#5fff5f bold",
    "error": "fg:#ff5f5f bold",
    "frame.border": "fg:#333333",
    "frame.label": "fg:#ffffff bold",
    "status-bar": "bg:#111111 fg:#888888",
    "side-panel": "fg:#cccccc",
    "completion-menu": "bg:#222222 fg:#ffffff",
    "completion-menu.completion.current": "bg:#E07A5F fg:#000000 bold",
    "completion-menu.meta.completion": "bg:#222222 fg:#888888",
    "completion-menu.meta.completion.current": "bg:#E07A5F fg:#000000",
})


def get_context_limit(model_name: str) -> int:
    model_name = model_name.lower()
    if "gemini" in model_name:
        return 1000000
    if "claude" in model_name or "sonnet" in model_name:
        return 200000
    if "gpt-4" in model_name:
        return 128000
    return 64000


def run_tui(
    ctx: Any,
    settings: Any,
    config_dir: Path,
    ai_service: Any,
    memory: Any,
    session_id: str
) -> None:
    """Run the premium full-screen Terminal User Interface (TUI)."""
    # Active states
    active_provider = settings.provider.active_provider or "none"
    provider_defaults = getattr(settings.provider, active_provider) if active_provider != "none" else None
    active_model = provider_defaults.model if provider_defaults else "none"
    cwd_name = Path.cwd().name

    try:
        provider = ai_service.get_provider()
    except Exception:
        provider = None

    # Billing and session stats
    billing_summary = get_billing_summary()
    total_cost = billing_summary.get("total_cost", 0.0)
    total_tokens = billing_summary.get("total_prompt_tokens", 0) + billing_summary.get("total_completion_tokens", 0)
    context_limit = get_context_limit(active_model)
    context_percent = min(100, int((total_tokens / context_limit) * 100))
    session_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    # Formatted chat history content
    formatted_history: List[List[tuple]] = []
    
    def get_history_content() -> List[tuple]:
        flat_list = []
        for msg_block in formatted_history:
            flat_list.extend(msg_block)
        return flat_list

    history_control = FormattedTextControl(get_history_content)
    
    # Custom scroll to bottom tracking
    def get_cursor_position() -> Point:
        lines_count = sum(len(block) for block in formatted_history)
        return Point(x=0, y=lines_count)

    history_control.get_cursor_position = get_cursor_position

    history_window = Window(
        content=history_control,
        wrap_lines=True,
    )

    # Input and Completer
    commands_with_meta = {
        "/help": "Show REPL help menu",
        "/clear": "Clear the terminal screen",
        "/init": "Scan workspace for context index",
        "/setup": "Interactive provider config wizard",
        "/switch": "Quick switch active AI provider & model",
        "/provider": "Manage AI providers (list/switch/test/models)",
        "/plan": "AI-generate Product Requirement Document (PRD)",
        "/architect": "AI-generate Architecture design document",
        "/code": "AI-generate project files with overwrite protection",
        "/review": "AI-perform code security and quality reviews",
        "/fix": "Surgically patch files with diff verification",
        "/memory": "Manage ADR decisions and knowledge base",
        "/test": "Run tests and trigger autonomous self-healing",
        "/pr": "Git auto-pilot commit and Pull Request creator",
        "/config": "Display or assign app configurations dynamically",
        "/tokens": "View token usage and estimated API cost dashboard",
        "/schema": "Scan workspace code structures and model/routes tree",
        "/refactor": "Refactor code files with rollback protection",
        "/docker": "Docker auto-pilot helper",
        "/voice": "Mic recording and audio transcription REPL chat",
        "/crawl": "Crawl documentation pages into knowledge base",
        "/exit": "Quit the interactive loop",
        "/quit": "Quit the interactive loop",
    }
    
    from zero.providers.registry import PROVIDER_CLASSES
    providers_list = list(PROVIDER_CLASSES.keys())
    completer = ZeroChatCompleter(commands_with_meta, providers_list, settings)

    # Processing Input
    async def process_input() -> None:
        user_input = input_field.text.strip()
        if not user_input:
            return
        
        # Clear input field immediately
        input_field.text = ""
        
        # 1. Handle TUI Slash Commands
        if user_input.startswith("/"):
            if user_input in ("/exit", "/quit"):
                app.exit()
                return
            elif user_input == "/clear":
                formatted_history.clear()
                app.invalidate()
                return
            elif user_input.startswith("/switch"):
                parts = user_input.split()
                if len(parts) < 2:
                    formatted_history.append([("class:error", "Error: Missing provider name. Usage: /switch <provider> [model]\n\n")])
                    app.invalidate()
                    return
                
                target_p = parts[1].lower()
                target_m = parts[2] if len(parts) > 2 else None
                
                try:
                    nonlocal active_provider, active_model, provider
                    # Update config & settings
                    settings.provider.active_provider = target_p
                    p_settings = getattr(settings.provider, target_p, None)
                    if p_settings and target_m:
                        p_settings.model = target_m
                    
                    from zero.services.config import save_config
                    save_config(settings, config_dir)
                    
                    # Reload active configurations
                    active_provider = target_p
                    active_model = target_m or (p_settings.model if p_settings else "none")
                    provider = ai_service.get_provider()
                    
                    formatted_history.append([("class:success", f"✓ Switched active provider to {active_provider} [{active_model}]\n\n")])
                except Exception as e:
                    formatted_history.append([("class:error", f"Error switching provider: {e}\n\n")])
                
                app.invalidate()
                return
            
            # Call standard fallback handler for other commands
            # We print output inside history block
            formatted_history.append([("class:system-text", f"Running command {user_input}...\n\n")])
            app.invalidate()
            return

        # 2. Standard prompt workflow
        # Append User query block
        formatted_history.append([("class:user-header", "User\n")])
        formatted_history.append([("class:user-text", f"{user_input}\n\n")])
        app.invalidate()

        # Database message logs
        user_msg_id = str(uuid.uuid4())[:8]
        try:
            memory.sessions.add_message(
                message_id=user_msg_id,
                session_id=session_id,
                role="user",
                content=user_input,
                token_count=provider.token_count(user_input) if provider else 0,
            )
        except Exception:
            pass

        # Build thought + response placeholder blocks
        thought_block: List[tuple] = [("class:thought", "+ Thought: ...")]
        response_block: List[tuple] = [("class:assistant-header", "\nZero Action Assistant\n"), ("class:assistant-text", "")]
        formatted_history.append(thought_block)
        formatted_history.append(response_block)
        app.invalidate()

        # Run AI stream completion
        history_msgs = memory.sessions.get_messages(session_id)
        system_prompt = ai_service.get_system_prompt(Path.cwd(), query=user_input)
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in history_msgs:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        assistant_response = ""
        start_time = time.time()
        
        try:
            if provider:
                # Stream completion chunks asynchronously
                async for chunk in provider.stream(api_messages):
                    assistant_response += chunk
                    # Update response block
                    response_block[1] = ("class:assistant-text", assistant_response + "\n\n")
                    app.invalidate()
                
                # Calculate thought speed duration
                duration_ms = int((time.time() - start_time) * 1000)
                thought_block[0] = ("class:thought", f"+ Thought: {duration_ms}ms\n")
            else:
                response_block[1] = ("class:error", "Error: No active AI provider connection established.\n\n")
        except Exception as e:
            response_block[1] = ("class:error", f"API Completion Error: {e}\n\n")

        app.invalidate()

        # Save assistant response to memory
        if assistant_response:
            assistant_msg_id = str(uuid.uuid4())[:8]
            try:
                memory.sessions.add_message(
                    message_id=assistant_msg_id,
                    session_id=session_id,
                    role="assistant",
                    content=assistant_response,
                    token_count=provider.token_count(assistant_response) if provider else 0,
                )
            except Exception:
                pass

        # Refresh stats
        nonlocal total_cost, total_tokens, context_percent
        new_billing = get_billing_summary()
        total_cost = new_billing.get("total_cost", 0.0)
        total_tokens = new_billing.get("total_prompt_tokens", 0) + new_billing.get("total_completion_tokens", 0)
        context_percent = min(100, int((total_tokens / context_limit) * 100))
        app.invalidate()

    def _accept_handler(buffer: Any) -> bool:
        asyncio.create_task(process_input())
        return True

    input_field = TextArea(
        height=3,
        multiline=False,
        prompt="Ask anything... ",
        completer=completer,
        history=None,
        accept_handler=_accept_handler
    )

    # Dynamic containers
    def get_main_layout() -> Any:
        # If history is empty, show mockup startup screen
        if not formatted_history:
            return HSplit([
                Window(),  # Top Spacer
                
                # Zero Action Title Logo
                Window(content=FormattedTextControl(HTML(
                    "<bold><cyan>"
                    " ______ ______ _____   ____  \n"
                    " |___  /|  ____|  __ \\ / __ \\ \n"
                    "    / / | |__  | |__) | |  | |\n"
                    "   / /  |  __| |  _  /| |  | |\n"
                    "  / /__ | |____| | \\ \\| |__| |\n"
                    " /_____||______|_|  \\_\\\\____/ "
                    "</cyan></bold>"
                )), align=WindowAlign.CENTER, height=6),
                
                Window(height=1),
                
                # Center input box
                VSplit([
                    Window(width=15),
                    Frame(
                        body=HSplit([
                            input_field,
                            Window(content=FormattedTextControl(HTML(
                                f"<blue>Build</blue> · <b>{active_model}</b> <gray>{active_provider}</gray> · <orange>high</orange>"
                            )), height=1)
                        ]),
                    ),
                    Window(width=15),
                ], height=6),
                
                Window(height=1),
                Window(content=FormattedTextControl(HTML(
                    "<gray><b>tab</b> agents  <b>ctrl+p</b> commands</gray>"
                )), align=WindowAlign.CENTER, height=1),
                
                Window(height=1),
                Window(content=FormattedTextControl(HTML(
                    "<orange>• Tip</orange> Create <bold>opencode.json</bold> for server settings"
                )), align=WindowAlign.CENTER, height=1),
                
                Window(),  # Bottom Spacer
                
                # Bottom status bar
                VSplit([
                    Window(content=FormattedTextControl(HTML(f" <blue>{cwd_name}</blue>"))),
                    Window(content=FormattedTextControl(HTML("<gray>1.0.0 </gray>")), align=WindowAlign.RIGHT),
                ], height=1)
            ])
            
        # Else, show split chat screen
        return VSplit([
            # Chat and input panel (75% width)
            HSplit([
                history_window,
                Frame(
                    body=HSplit([
                        input_field,
                        Window(content=FormattedTextControl(HTML(
                            f"<blue>Build</blue> · <b>{active_model}</b> <gray>{active_provider}</gray> · <orange>high</orange>"
                        )), height=1)
                    ])
                )
            ], width=Dimension(weight=3)),
            
            # Border Separator
            Window(width=1, char="│", style="class:line"),
            
            # Side Info Panel (25% width)
            HSplit([
                Window(height=1),
                Window(content=FormattedTextControl(HTML(
                    f" <gray>New session - {session_time}</gray>\n"
                )), height=2),
                
                Window(content=FormattedTextControl(HTML(
                    " <b>Context</b>\n"
                    f" <cyan>{total_tokens:,} tokens</cyan>\n"
                    f" <gray>{context_percent}% used</gray>\n"
                    f" <green>${total_cost:.4f} spent</green>\n"
                )), height=5),
                
                Window(content=FormattedTextControl(HTML(
                    " <b>LSP</b>\n"
                    " <gray>LSPs are disabled</gray>\n"
                )), height=3),
                
                Window(),  # Vertical Spacer
                
                # Bottom Status
                VSplit([
                    Window(content=FormattedTextControl(HTML(f" <blue>/{cwd_name}</blue>"))),
                    Window(content=FormattedTextControl(HTML("<gray>• Zero Action 1.0.0 </gray>")), align=WindowAlign.RIGHT),
                ], height=1)
            ], width=Dimension(weight=1))
        ])

    root_container = DynamicContainer(get_main_layout)

    # Key Bindings
    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("c-d")
    def _exit(event: Any) -> None:
        event.app.exit()

    app: Application = Application(
        layout=Layout(root_container, focused_element=input_field),
        key_bindings=kb,
        style=tui_style,
        full_screen=True,
    )

    # Run application
    app.run()
