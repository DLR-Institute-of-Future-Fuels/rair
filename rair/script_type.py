"""Detection of the interpreter for running a script."""

import os
import shlex
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import Optional

# Files that are executed directly
EXECUTABLE_EXTENSIONS = {".bat", ".cmd", ".exe"}

# Interpreters (in order of preference) for scripts without a usable shebang line
EXTENSION_INTERPRETERS: dict[str, list[list[str]]] = {
    ".sh": [["bash"], ["sh"]],
    ".bash": [["bash"]],
    ".ps1": [["pwsh", "-File"], ["powershell", "-File"]],
    ".r": [["Rscript"]],
    ".jl": [["julia"]],
    ".js": [["node"]],
    ".mjs": [["node"]],
    ".pl": [["perl"]],
    ".rb": [["ruby"]],
    ".lua": [["lua"]],
    ".php": [["php"]],
}

SCRIPT_EXTENSIONS = {".py"} | EXECUTABLE_EXTENSIONS | set(EXTENSION_INTERPRETERS)

# A Python interpreter in these directories is not meant as a specific
# installation, e.g. "#!/usr/bin/python3"
SYSTEM_DIRS = {"/bin", "/usr/bin", "/usr/local/bin"}


def _is_usable(executable: str) -> bool:
    """Check if a name found on the PATH is a usable executable."""
    path = shutil.which(executable)
    if path is None:
        return False
    # Windows places stubs here that only point to the Microsoft Store
    return not (os.name == "nt" and "\\microsoft\\windowsapps\\" in path.lower())


def find_python() -> str:
    """Find the Python interpreter for running a script.

    This is the interpreter a user gets by typing `python` in the shell, so
    that the packages of an activated virtual environment are available to the
    script. The interpreter running rair itself may live in an isolated
    environment (e.g. pipx) and is only used as fallback.

    Returns:
        Name of the interpreter on the PATH or path to the fallback interpreter
    """
    for name in ("python", "python3"):
        if _is_usable(name):
            return name
    return sys.executable


def parse_shebang(script_path: Path) -> Optional[list[str]]:
    """Read the interpreter and its arguments from the shebang line of a script.

    A leading `/usr/bin/env` is removed, so that "#!/usr/bin/env python3"
    gives ["python3"].

    Args:
        script_path: Path to the script file

    Returns:
        Interpreter and its arguments or None if there is no shebang line
    """
    try:
        with open(script_path, "rb") as f:
            first_line = f.readline(512)
    except OSError:
        return None

    if not first_line.startswith(b"#!"):
        return None

    try:
        parts = shlex.split(first_line[2:].decode("utf-8", errors="ignore"))
    except ValueError:
        return None

    if parts and PurePosixPath(parts[0]).name == "env":
        # Skip options and variable assignments of env
        parts = parts[1:]
        while parts and (parts[0].startswith("-") or "=" in parts[0]):
            parts = parts[1:]

    return parts or None


def _resolve_shebang(shebang: list[str]) -> Optional[list[str]]:
    """Get the command for the interpreter of a shebang line.

    Returns:
        Command and arguments or None if the interpreter is not available
    """
    interpreter = PurePosixPath(shebang[0])
    interpreter_args = shebang[1:]
    name = interpreter.name
    has_directory = "/" in shebang[0]

    if has_directory and str(interpreter.parent) not in SYSTEM_DIRS:
        # A specific installation, e.g. the interpreter of a virtual environment
        if Path(shebang[0]).is_file():
            return shebang
    elif name in ("python", "python3"):
        return [find_python()] + interpreter_args
    elif name.startswith("python") and not _is_usable(name):
        # A versioned interpreter like python3.11 that is not installed
        return [find_python()] + interpreter_args

    if _is_usable(name):
        return [name] + interpreter_args
    if has_directory and Path(shebang[0]).is_file():
        return shebang
    return None


def get_script_command(script_path: Path) -> list[str]:
    """Get the command and arguments for running a script.

    The interpreter is taken from the shebang line of the script. Without a
    shebang line, or if its interpreter is not available (e.g. "/bin/bash" on
    Windows), it is chosen by the file extension. Other files are executed
    directly.

    Args:
        script_path: Path to the script file

    Returns:
        List of command and arguments to run the script
    """
    ext = script_path.suffix.lower()

    if ext not in EXECUTABLE_EXTENSIONS:
        shebang = parse_shebang(script_path)
        if shebang is not None:
            command = _resolve_shebang(shebang)
            if command is not None:
                return command + [str(script_path)]

        if ext == ".py":
            return [find_python(), str(script_path)]

        if ext in EXTENSION_INTERPRETERS:
            candidates = EXTENSION_INTERPRETERS[ext]
            for candidate in candidates:
                if _is_usable(candidate[0]):
                    return candidate + [str(script_path)]
            return candidates[0] + [str(script_path)]

    if os.name != "nt" and script_path.parent == Path():
        # Without directory the file would be searched on the PATH
        return [os.path.join(os.curdir, str(script_path))]
    return [str(script_path)]
