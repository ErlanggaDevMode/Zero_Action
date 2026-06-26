"""Type-safe CLI context state for Zero Action CLI commands."""

from dataclasses import dataclass
from pathlib import Path
from zero.services.config import ZeroSettings


@dataclass
class CliContext:
    """Type-safe container for options passed through Typer callback context."""

    settings: ZeroSettings
    debug: bool
    config_dir: Path
