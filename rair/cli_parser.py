"""CLI argument parsing utilities for rair."""

from typing import Tuple

SCRIPT_EXTENSIONS = {".py", ".sh", ".bash", ".bat", ".cmd", ".exe", ".ps1"}

RAIR_OPTIONS = {
    "--config",
    "--input",
    "--output",
    "--exclude",
    "--archive-dir",
}

RAIR_BOOLEAN_OPTIONS = {
    "--capture-output",
    "--no-auto-discover",
}

ALL_RAIR_OPTIONS = RAIR_OPTIONS | RAIR_BOOLEAN_OPTIONS


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


def separate_args(args: list[str]) -> Tuple[list[str], list[str]]:
    """Separate rair options from script arguments.

    Uses "--" as a separator - everything after "--" goes to script arguments.

    Args:
        args: List of arguments to separate

    Returns:
        Tuple of (rair_options, script_arguments)
    """
    rair_options: list[str] = []
    script_arguments: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--":
            script_arguments.extend(args[i + 1 :])
            break

        if arg in RAIR_BOOLEAN_OPTIONS:
            rair_options.append(arg)
        elif arg in RAIR_OPTIONS:
            rair_options.append(arg)
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                rair_options.append(args[i + 1])
                i += 1
        else:
            script_arguments.append(arg)

        i += 1

    return rair_options, script_arguments