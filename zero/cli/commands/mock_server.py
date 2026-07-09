"""CLI subcommand and slash command to automatically generate and run a mock API server."""

import re
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from zero.services.ai import AIService

# Global reference to running background server
_bg_server: Optional[HTTPServer] = None
_bg_thread: Optional[threading.Thread] = None

class MockAPIHandler(BaseHTTPRequestHandler):
    mock_data: Dict[str, Any] = {}

    def log_message(self, format, *args):
        # Override to prevent logging to stderr during tests/runs unless verbose
        pass

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")

    def do_PUT(self):
        self._handle_request("PUT")

    def do_DELETE(self):
        self._handle_request("DELETE")

    def do_PATCH(self):
        self._handle_request("PATCH")

    def _handle_request(self, method: str):
        path = self.path.split("?")[0]
        route_key = f"{method} {path}"
        
        # Exact match or default fallback
        response_body = self.mock_data.get(route_key)
        if response_body is None:
            # Try matching with path variables (wildcard / fallback)
            for key, val in self.mock_data.items():
                k_method, k_path = key.split(" ", 1)
                if k_method == method:
                    # Convert flask/fastapi path variables to regex
                    pattern = re.sub(r'<[^>]+>', '[^/]+', k_path)
                    pattern = re.sub(r'\{[^}]+\}', '[^/]+', pattern)
                    if re.match(f"^{pattern}$", path):
                        response_body = val
                        break

        if response_body is not None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": f"Not Found: {method} {path}"}).encode("utf-8"))


def detect_routes(workspace: Path) -> List[Dict[str, str]]:
    """Scan python files in workspace for route definitions."""
    routes: List[Dict[str, str]] = []
    # Match @app.get("/path"), @router.post('/path'), @app.route("/path", methods=["GET"])
    route_regex = re.compile(r'@(?:app|router|api|blueprint)\.(get|post|put|delete|patch|route)\(\s*[\'"]([^\'"]+)[\'"]')
    
    extensions = {".py"}
    for path in sorted(workspace.rglob("*")):
        if any(part.startswith((".", "__")) for part in path.parts):
            continue
        if path.is_file() and path.suffix in extensions:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for match in route_regex.finditer(content):
                    method = match.group(1).upper()
                    route_path = match.group(2)
                    if method == "ROUTE":
                        # Assume GET as default for .route()
                        method = "GET"
                    
                    # Deduplicate
                    if not any(r["path"] == route_path and r["method"] == method for r in routes):
                        routes.append({"method": method, "path": route_path})
            except Exception:
                pass
    return routes


def generate_mock_data(routes: List[Dict[str, str]], provider: Any) -> Dict[str, Any]:
    """Call LLM to generate realistic mock JSON data for detected routes."""
    if not routes:
        return {
            "GET /api/users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "GET /api/products": [{"id": 101, "name": "Widget A", "price": 9.99}],
            "GET /api/health": {"status": "healthy"}
        }

    endpoints_desc = ", ".join(f"{r['method']} {r['path']}" for r in routes)
    system_prompt = (
        "You are an API mocking assistant. Generate a single valid JSON object containing realistic mock responses "
        "for the following endpoints. The keys of the JSON object must be exactly 'METHOD /path' (e.g. 'GET /users'). "
        "The values must be realistic mock response bodies (objects or lists). "
        "Return ONLY the raw JSON object, no markdown formatting, no code blocks, no other text."
    )
    user_prompt = f"Endpoints: {endpoints_desc}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw_response = provider.chat(messages)
        # Strip potential code fences if AI ignored instructions
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_response = "\n".join(lines).strip()
            
        return json.loads(raw_response)
    except Exception:
        # Fallback in case of parsing/LLM errors
        fallback = {}
        for r in routes:
            fallback[f"{r['method']} {r['path']}"] = {"status": "mocked", "method": r["method"], "path": r["path"]}
        return fallback


def mock_server(
    ctx: typer.Context,
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the mock server on"),
    background: bool = typer.Option(False, "--background", "-b", help="Run the server in the background"),
    stop: bool = typer.Option(False, "--stop", help="Stop the background server if running"),
) -> None:
    """Scan project endpoints and spin up a mock API server with realistic data."""
    global _bg_server, _bg_thread
    console = Console()
    
    if stop:
        if _bg_server:
            _bg_server.shutdown()
            _bg_server.server_close()
            _bg_server = None
            _bg_thread = None
            console.print("[green]✓ Background mock server stopped successfully.[/green]")
        else:
            console.print("[yellow]No active background mock server found.[/yellow]")
        return

    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # 1. Detect routes in workspace
    routes = detect_routes(Path.cwd())
    console.print(f"[cyan]Detected {len(routes)} routes in the workspace.[/cyan]")

    # 2. Get provider & generate mock data
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
        console.print("[yellow]Generating mock data using AI...[/yellow]")
        mock_data = generate_mock_data(routes, provider)
    except Exception as e:
        console.print(f"[yellow]Could not generate mock data with LLM ({e}). using offline fallbacks...[/yellow]")
        mock_data = generate_mock_data([], None)

    # Configure handler
    MockAPIHandler.mock_data = mock_data

    # 3. Start server
    try:
        server = HTTPServer(("localhost", port), MockAPIHandler)
    except Exception as e:
        console.print(f"[bold red]Failed to start server on port {port}:[/bold red] {e}")
        raise typer.Exit(code=1)

    panel_text = (
        f"Mock Server running at: [bold green]http://localhost:{port}[/bold green]\n\n"
        "[bold cyan]Active Endpoints:[/bold cyan]\n" +
        "\n".join(f"  - {key}" for key in mock_data.keys())
    )

    if background:
        if _bg_server:
            console.print("[yellow]Stopping existing background server...[/yellow]")
            _bg_server.shutdown()
            _bg_server.server_close()
        
        _bg_server = server
        _bg_thread = threading.Thread(target=server.serve_forever, daemon=True)
        _bg_thread.start()
        console.print(Panel(panel_text + "\n\n[dim]Server is running in background. Use 'zero mock --stop' to terminate.[/dim]", title="[bold green]Mock Server (BG)[/bold green]"))
    else:
        console.print(Panel(panel_text + "\n\n[bold yellow]Press Ctrl+C to stop the server.[/bold yellow]", title="[bold green]Mock Server[/bold green]"))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping mock server...[/yellow]")
            server.shutdown()
            server.server_close()
            console.print("[green]✓ Mock server stopped.[/green]")
