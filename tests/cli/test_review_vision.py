"""CLI integration tests for the visual review command."""

import os
from unittest.mock import patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


class MockDelta:
    def __init__(self, content):
        self.content = content


class MockChoice:
    def __init__(self, content):
        self.delta = MockDelta(content)


class MockChunk:
    def __init__(self, content):
        self.choices = [MockChoice(content)]


async def mock_async_stream(*args, **kwargs):
    yield MockChunk("Visual UI/UX audit report:\n")
    yield MockChunk("- Alignment: Good\n")
    yield MockChunk("- Color contrast: Pass\n")


@patch("litellm.acompletion")
def test_cli_review_vision_success(mock_acompletion, tmp_path, temp_zero_dir) -> None:
    """Test that zero review --vision successfully performs visual audit on image files."""
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

    # Create dummy image file (1x1 transparent PNG structure / simple bytes)
    mock_image = workspace / "mockup.png"
    mock_image.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDAT\x18Wc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82")

    old_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        # Mock LLM streaming completion
        mock_acompletion.side_effect = mock_async_stream
        
        result = runner.invoke(app, [
            "review",
            "--vision",
            "--file", "mockup.png"
        ])
        
        assert result.exit_code == 0
        assert "Visual UI/UX Reviewer" in result.stdout
        assert "Alignment: Good" in result.stdout
        assert "Color contrast: Pass" in result.stdout
    finally:
        os.chdir(old_cwd)
