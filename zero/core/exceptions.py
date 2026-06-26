"""Core exceptions for Zero Action."""

class ZeroError(Exception):
    """Base exception for all Zero Action errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(ZeroError):
    """Raised when there is an issue loading or validating configurations."""
    pass


class LoggingError(ZeroError):
    """Raised when the logging system fails to initialize."""
    pass
