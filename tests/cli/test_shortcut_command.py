"""CLI integration tests for the shortcut command."""

from unittest.mock import patch
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


def test_cli_shortcut_flow(tmp_path, temp_zero_dir) -> None:
    """Test that zero shortcut list, add, and remove operations update shell profiles correctly."""
    mock_profile = tmp_path / "mock_profile.ps1"
    
    with patch("zero.cli.commands.shortcut._get_shell_profiles", return_value=[mock_profile]):
        # 1. List aliases (should be empty initially)
        list_result = runner.invoke(app, ["shortcut", "list"])
        assert list_result.exit_code == 0
        assert "No custom shell shortcuts configured" in list_result.stdout
        
        # 2. Add an alias
        add_result = runner.invoke(app, [
            "shortcut", "add",
            "-n", "zask",
            "-c", "ask"
        ])
        assert add_result.exit_code == 0
        assert "Successfully added shortcut" in add_result.stdout
        
        # Verify content was written to mock profile
        assert mock_profile.exists()
        content = mock_profile.read_text(encoding="utf-8")
        assert "ZERO ACTION ALIASES START" in content
        assert "zask" in content
        assert "zero ask" in content
        assert "ZERO ACTION ALIASES END" in content
        
        # 3. List aliases (should show the added one)
        list_result2 = runner.invoke(app, ["shortcut", "list"])
        assert list_result2.exit_code == 0
        assert "zask" in list_result2.stdout
        
        # 4. Remove the alias
        remove_result = runner.invoke(app, [
            "shortcut", "remove",
            "-n", "zask"
        ])
        assert remove_result.exit_code == 0
        assert "Successfully removed shortcut" in remove_result.stdout
        
        # Verify block is empty of aliases
        content_after = mock_profile.read_text(encoding="utf-8")
        assert "zask" not in content_after
