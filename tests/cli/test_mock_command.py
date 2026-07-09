"""CLI integration tests for the mock command."""

import os
import urllib.request
import json
import time
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


@patch("litellm.completion")
def test_cli_mock_server_flow(mock_completion, tmp_path, temp_zero_dir) -> None:
    """Test that zero mock successfully starts a server, handles requests, and stops."""
    providers_toml = temp_zero_dir / "providers.toml"
    providers_toml.write_text("""
[provider]
active_provider = "openai"
[provider.openai]
api_key = "sk-test"
base_url = "https://api.openai.com/v1"
model = "gpt-4"
""", encoding="utf-8")

    workspace = tmp_path / "mock_project"
    workspace.mkdir()

    # Create dummy python file with a route
    dummy_file = workspace / "routes.py"
    dummy_file.write_text('@app.get("/api/test")\ndef test_route():\n    pass\n', encoding="utf-8")

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM chat response to return valid mock data JSON
        mock_response_data = {
            "GET /api/test": {"status": "ok", "message": "hello test"}
        }
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(mock_response_data)))]
        )
        
        # Start server on port 8002 in background
        start_result = runner.invoke(app, [
            "mock",
            "--port", "8002",
            "--background"
        ])
        
        assert start_result.exit_code == 0
        assert "Mock Server running at" in start_result.stdout
        
        # Wait a small moment for server to start serving
        time.sleep(0.5)
        
        # Fetch from mock server
        try:
            req = urllib.request.Request("http://localhost:8002/api/test")
            with urllib.request.urlopen(req, timeout=2) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)
                assert data == {"status": "ok", "message": "hello test"}
        finally:
            # Always make sure to stop the server so port is released
            stop_result = runner.invoke(app, [
                "mock",
                "--stop"
            ])
            assert stop_result.exit_code == 0
            assert "stopped successfully" in stop_result.stdout
            
    finally:
        os.chdir(old_cwd)
