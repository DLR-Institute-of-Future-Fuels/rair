"""CLI argument parsing utilities for rair."""

from pathlib import Path

from .script_type import SCRIPT_EXTENSIONS, parse_shebang


def is_script_extension(value: str) -> bool:
    """Check if a value has a known script extension.

    Args:
        value: String value to check

    Returns:
        True if value has a known script extension
    """
    for ext in SCRIPT_EXTENSIONS:
        if value.lower().endswith(ext):
            return True
    return False


def is_script(value: str) -> bool:
    """Check if a value is a script to run instead of a command.

    Args:
        value: String value to check

    Returns:
        True if value has a known script extension or is a file with a shebang line
    """
    if is_script_extension(value):
        return True
    path = Path(value)
    return path.is_file() and parse_shebang(path) is not None
