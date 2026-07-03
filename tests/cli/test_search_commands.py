from unittest.mock import patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()

@patch("zero.services.search.search_ddg")
def test_search_command_output(mock_search_ddg) -> None:
    mock_search_ddg.return_value = [
        {"title": "FastAPI", "url": "https://fastapi.org", "snippet": "FastAPI is fast."}
    ]
    result = runner.invoke(app, ["search", "fastapi"])
    assert result.exit_code == 0
    assert "Web Search Results" in result.stdout
    assert "FastAPI" in result.stdout
    assert "https://fastapi.org" in result.stdout

@patch("zero.services.search.fetch_url_text")
def test_read_command_output(mock_fetch_url_text) -> None:
    mock_fetch_url_text.return_value = "This is webpage content text."
    result = runner.invoke(app, ["read", "https://example.com"])
    assert result.exit_code == 0
    assert "Webpage Context" in result.stdout
    assert "This is webpage content text." in result.stdout
