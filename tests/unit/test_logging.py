"""Unit tests for log initialization, routing, and secret masking."""

from pathlib import Path
from loguru import logger
from zero.services.logging import setup_logging


def test_logging_setup_and_routing(temp_zero_dir: Path) -> None:
    """Test that logs are correctly initialized and routed based on category."""
    log_dir = temp_zero_dir / "logs"
    setup_logging(log_dir, debug_mode=True)

    # Trigger different logs
    logger.bind(category="cli").info("This is a CLI log entry.")
    logger.bind(category="provider").debug("This is a Provider log entry.")
    logger.bind(category="git").warning("This is a Git warning entry.")
    logger.info("This is a general log entry.")

    # Remove logger to close files so they can be read
    logger.remove()

    # Verify category files created
    assert (log_dir / "cli.log").exists()
    assert (log_dir / "provider.log").exists()
    assert (log_dir / "git.log").exists()
    assert (log_dir / "zero.log").exists()

    # Check CLI log content
    with open(log_dir / "cli.log", "r", encoding="utf-8") as f:
        cli_content = f.read()
    assert "This is a CLI log entry." in cli_content
    assert "This is a Provider log entry." not in cli_content

    # Check Provider log content
    with open(log_dir / "provider.log", "r", encoding="utf-8") as f:
        provider_content = f.read()
    assert "This is a Provider log entry." in provider_content
    assert "This is a CLI log entry." not in provider_content

    # Check zero.log (contains everything)
    with open(log_dir / "zero.log", "r", encoding="utf-8") as f:
        zero_content = f.read()
    assert "This is a CLI log entry." in zero_content
    assert "This is a Provider log entry." in zero_content
    assert "This is a Git warning entry." in zero_content
    assert "This is a general log entry." in zero_content


def test_logging_masks_secrets(temp_zero_dir: Path) -> None:
    """Test that logging patches log messages to mask API keys and credentials."""
    log_dir = temp_zero_dir / "logs"
    setup_logging(log_dir, debug_mode=True)

    # Log sensitive information
    logger.info("Connecting with api_key = \"sk-1234567890abcdef1234567890abcdef\"")
    logger.info("Checking token: 'some-token-string'")
    logger.info("Direct raw key: sk-ant-sid1234567890abcdef1234")
    logger.info("Direct google key: AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q")

    logger.remove()

    with open(log_dir / "zero.log", "r", encoding="utf-8") as f:
        content = f.read()

    # Verify everything was masked correctly
    assert "sk-1234567890abcdef1234567890abcdef" not in content
    assert "sk-ant-sid1234567890abcdef1234" not in content
    assert "AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q" not in content
    assert "******" in content
