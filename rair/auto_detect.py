"""Auto-discovery of input and output files for rair."""

from pathlib import Path
from typing import Optional, Set


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Truncated 20-char hash, or empty string if file doesn't exist
    """
    if not file_path.exists():
        return ""

    from .hashing import compute_file_hash as _compute_file_hash
    return _compute_file_hash(file_path)


def get_file_hash_map(files: list[Path]) -> dict[Path, str]:
    """Get hash map for multiple files.

    Args:
        files: List of file paths

    Returns:
        Mapping of file_path → hash (excludes non-existent files)
    """
    result: dict[Path, str] = {}
    for file_path in files:
        hash_val = compute_file_hash(file_path)
        if hash_val:
            result[file_path] = hash_val
    return result


def get_hidden_dirs(base_dir: Path) -> set[Path]:
    """Get all hidden directories (directories starting with '.').

    Args:
        base_dir: Base directory to search

    Returns:
        Set of hidden directory paths
    """
    return {p for p in base_dir.rglob("*") if p.is_dir() and p.name.startswith(".")}


def is_hidden_file(file_path: Path) -> bool:
    """Check if a file name starts with a dot.

    Args:
        file_path: Path to check

    Returns:
        True if file name starts with '.'
    """
    return file_path.name.startswith('.')


def is_in_hidden_directory(file_path: Path, base_dir: Path) -> bool:
    """Check if a file is in a hidden directory (any parent starts with '.').

    Args:
        file_path: Path to check
        base_dir: Base directory to resolve from

    Returns:
        True if any parent directory name starts with '.'
    """
    try:
        relative_path = file_path.relative_to(base_dir)
        for part in relative_path.parts:
            if part.startswith('.'):
                return True
        return False
    except ValueError:
        return False


def get_auto_discover_candidates(
    base_dir: Path,
    tracked_files: Optional[list[Path]] = None,
) -> list[Path]:
    """Get files that should be auto-discovered (not hidden, not git-tracked).

    Args:
        base_dir: Directory to search in
        tracked_files: List of git-tracked files to exclude

    Returns:
        List of files that are candidates for auto-discovery
    """
    if tracked_files is None:
        tracked_files = []

    tracked_set: Set[Path] = set(tracked_files)
    candidates: list[Path] = []

    for item in base_dir.rglob("*"):
        if item.is_file():
            if is_hidden_file(item):
                continue

            if is_in_hidden_directory(item, base_dir):
                continue

            if item in tracked_set:
                continue

            candidates.append(item)

    return candidates


def should_exclude_file(
    file_path: Path,
    base_dir: Path,
    archive_dir: Path,
    hidden_dirs: set[Path],
    tracked_files: Optional[list[Path]] = None,
) -> bool:
    """Check if file should be excluded from auto-discovery.

    Args:
        file_path: File path to check
        base_dir: Base directory
        archive_dir: Archive directory path
        hidden_dirs: Set of hidden directory paths
        tracked_files: Optional list of git-tracked files

    Returns:
        True if file should be excluded
    """
    if is_hidden_file(file_path):
        return True

    if is_in_hidden_directory(file_path, base_dir):
        return True

    try:
        if file_path.is_relative_to(archive_dir):
            return True
    except ValueError:
        pass

    if tracked_files is not None:
        try:
            if file_path in tracked_files:
                return True
        except ValueError:
            pass

    return False


def categorize_files_by_changes(
    before_hashes: dict[Path, str],
    after_hashes: dict[Path, str],
) -> tuple[list[Path], list[Path]]:
    """Categorize files as input/output based on hash changes.

    Args:
        before_hashes: File hashes before execution
        after_hashes: File hashes after execution

    Returns:
        (input_files, output_files)
        - input: Files with same hash in both (unchanged)
        - output: Files with different hash OR created during execution
        - deleted: Ignored
    """
    input_files: list[Path] = []
    output_files: list[Path] = []

    for file_path, before_hash in before_hashes.items():
        if file_path in after_hashes:
            if before_hash == after_hashes[file_path]:
                input_files.append(file_path)
            else:
                output_files.append(file_path)

    for file_path in after_hashes:
        if file_path not in before_hashes:
            output_files.append(file_path)

    return input_files, output_files