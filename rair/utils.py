"""Shared utility functions for rair."""

import json
from pathlib import Path
from typing import Any

HASH_LENGTH = 20


def safe_load_json(file_path: Path, default: Any = None) -> Any:
    """Safely load JSON file with error handling.

    Args:
        file_path: Path to JSON file
        default: Default value to return if file doesn't exist or can't be parsed

    Returns:
        Parsed JSON data or default value
    """
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def safe_write_json(file_path: Path, data: Any, create_dirs: bool = True) -> None:
    """Safely write JSON file with optional directory creation.

    Args:
        file_path: Path to write JSON file
        data: Data to serialize as JSON
        create_dirs: Create parent directories if they don't exist
    """
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2 if file_path.suffix != ".json" else None)


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if needed.

    Args:
        path: Directory path to ensure exists

    Returns:
        Path object for the directory
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_hidden(path: Path | str) -> bool:
    """Check if path is hidden (name starts with '.').

    Args:
        path: Path or string to check

    Returns:
        True if path name starts with '.'
    """
    name = path.name if isinstance(path, Path) else Path(path).name
    return name.startswith('.')


def hash_to_short(hash_value: str) -> str:
    """Truncate hash to standard length.

    Args:
        hash_value: Full hash string

    Returns:
        Truncated hash (20 characters)
    """
    return hash_value[:HASH_LENGTH]