"""Script type detection for rair."""

from pathlib import Path
from typing import Tuple


def detect_script_type(script_path: Path) -> str:
    """Detect the script type based on extension and shebang.

    Args:
        script_path: Path to the script file

    Returns:
        Type of script: "python", "bash", or "other"
    """
    ext = script_path.suffix.lower()

    if ext == ".py":
        return "python"

    if ext == ".sh":
        return "bash"

    if ext in [".bat", ".cmd", ".exe"]:
        return "other"

    try:
        with open(script_path, "rb") as f:
            first_line = f.readline(100)
            shebang = first_line.decode("utf-8", errors="ignore")
            if shebang.startswith("#!"):
                if "python" in shebang.lower():
                    return "python"
                if "bash" in shebang.lower():
                    return "bash"
    except (OSError, UnicodeDecodeError):
        pass

    return "other"


def get_command_args(script_path: Path, script_type: str) -> list[str]:
    """Get the command and arguments for running a script.

    Args:
        script_path: Path to the script file
        script_type: Type of script ("python", "bash", or "other")

    Returns:
        List of command and arguments to run the script
    """
    if script_type == "python":
        return ["python", str(script_path)]

    if script_type == "bash":
        return ["bash", str(script_path)]

    return [str(script_path)]


def get_run_command(script_path: Path) -> Tuple[list[str], str]:
    """Get the command to execute a script and its type.

    Args:
        script_path: Path to the script file

    Returns:
        Tuple of (command list, script type string)
    """
    script_type = detect_script_type(script_path)
    command = get_command_args(script_path, script_type)
    return command, script_type


def make_executable(script_path: Path) -> bool:
    """Make a script executable (Unix-like permissions).

    Args:
        script_path: Path to the script file

    Returns:
        True if successful, False otherwise
    """
    import stat

    try:
        current_mode = script_path.stat().st_mode
        new_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IEXEC
        script_path.chmod(new_mode)
        return True
    except (OSError, AttributeError):
        return False