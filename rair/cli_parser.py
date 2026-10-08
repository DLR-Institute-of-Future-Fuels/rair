"""CLI argument parsing utilities for rair."""

SCRIPT_EXTENSIONS = {".py", ".sh", ".bash", ".bat", ".cmd", ".exe", ".ps1"}


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
