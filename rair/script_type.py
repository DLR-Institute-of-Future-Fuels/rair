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
                if "sh" in shebang.lower():
                    return "sh"
    except (OSError, UnicodeDecodeError):
        pass

    if ext == ".sh":
        return "bash"

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
