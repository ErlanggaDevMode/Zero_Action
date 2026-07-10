"""CLI integration tests for memory backup and restore commands."""

import zipfile
from typer.testing import CliRunner
from zero.cli.app import app

runner = CliRunner()


def test_cli_memory_backup_restore_flow(tmp_path, temp_zero_dir) -> None:
    """Test that zero memory backup and restore correctly packages and extracts config directory files."""
    # 1. Ensure config files exist in temp_zero_dir
    settings_toml = temp_zero_dir / "settings.toml"
    settings_toml.write_text("active_provider = \"openai\"", encoding="utf-8")
    
    # 2. Run backup command
    backup_zip = tmp_path / "my_backup.zip"
    backup_result = runner.invoke(app, [
        "memory", "backup",
        "--output", str(backup_zip)
    ])
    
    assert backup_result.exit_code == 0
    assert backup_zip.exists()
    
    # Check that zip file contains settings.toml
    with zipfile.ZipFile(backup_zip, "r") as zf:
        namelist = zf.namelist()
        assert "settings.toml" in namelist
        
    # 3. Modify settings.toml locally, then run restore to revert
    settings_toml.write_text("active_provider = \"modified\"", encoding="utf-8")
    
    restore_result = runner.invoke(app, [
        "memory", "restore",
        str(backup_zip)
    ], input="y\n")  # Auto-confirm overwrite prompt
    
    assert restore_result.exit_code == 0
    
    # Check that settings.toml is restored to original state
    restored_content = settings_toml.read_text(encoding="utf-8")
    assert "active_provider = \"openai\"" in restored_content
