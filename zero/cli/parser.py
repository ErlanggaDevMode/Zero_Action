"""Option parser and validation utilities for CLI Layer."""

import typer


def validate_positive_int(value: int) -> int:
    """Validate that the integer value is strictly positive.

    Args:
        value: The integer value to check.

    Returns:
        int: The validated positive integer.

    Raises:
        typer.BadParameter: If the value is not positive.
    """
    if value <= 0:
        raise typer.BadParameter("Value must be a positive integer.")
    return value
