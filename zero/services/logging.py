"""Logging service for Zero Action.

Sets up console logger and routes file logs to category-specific files.
Applies global patching to prevent leaking credentials in logs.
"""

import re
import sys
from pathlib import Path
from loguru import logger
from zero.core.exceptions import LoggingError

# Patterns to match key-value secrets
SECRET_PATTERN = re.compile(
    r'(?i)(api_key|token|password|secret|jwt|credential|auth)([\s:=]+)(["\'\w\-]{4,})'
)

# Patterns to match raw API keys
RAW_KEY_PATTERN = re.compile(
    r'\b(sk-[a-zA-Z0-9\-_]{15,}|AIzaSy[a-zA-Z0-9\-_]{33})\b'
)


def _sanitize_record(record) -> None:
    """Patch the log record to mask any credentials/secrets before logging.

    Args:
        record: The Loguru log record dictionary to modify in-place.
    """
    message = record["message"]
    if isinstance(message, str) and message:
        # Mask pattern key=val or key:val
        sanitized = SECRET_PATTERN.sub(r'\1\2"******"', message)
        # Mask raw api keys (e.g. sk-..., AIzaSy...)
        sanitized = RAW_KEY_PATTERN.sub("******", sanitized)
        record["message"] = sanitized


def setup_logging(log_dir: Path, debug_mode: bool = False) -> None:
    """Configure Loguru console and routed file logs.

    Files are stored in log_dir. Log category routing is determined by
    calling `logger.bind(category="category_name")`.

    Args:
        log_dir: Path to directory where logs will be stored.
        debug_mode: If True, set console level to DEBUG; otherwise INFO.

    Raises:
        LoggingError: If setup fails.
    """
    try:
        # Clear default handlers
        logger.remove()

        # Console logging format and level
        console_level = "DEBUG" if debug_mode else "INFO"
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level:8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

        logger.add(
            sys.stderr,
            level=console_level,
            format=console_format,
            backtrace=debug_mode,
            diagnose=debug_mode,
        )

        # Ensure logs directory exists
        log_dir.mkdir(parents=True, exist_ok=True)

        categories = ["cli", "provider", "ai", "memory", "git", "error", "plugin"]
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:8} | "
            "{name}:{function}:{line} | {message}"
        )

        # Register category file handlers
        for category in categories:
            log_file = log_dir / f"{category}.log"

            # Create a localized closure for the filter
            def make_filter(cat: str):
                return lambda record: record["extra"].get("category") == cat

            logger.add(
                str(log_file),
                level="DEBUG",
                format=file_format,
                filter=make_filter(category),
                rotation="10 MB",
                retention="30 days",
                compression="zip",
                encoding="utf-8",
            )

        # Catch-all log file (zero.log) containing all events
        logger.add(
            str(log_dir / "zero.log"),
            level="DEBUG",
            format=file_format,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
        )

        # Configure the patcher globally
        logger.configure(patcher=_sanitize_record)

    except Exception as e:
        raise LoggingError(f"Failed to setup logging in {log_dir}: {e}") from e
