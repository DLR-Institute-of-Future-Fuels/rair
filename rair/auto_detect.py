"""Auto-discovery of input and output files for rair."""

from pathlib import Path
from typing import Optional, Generator
from .hashing import compute_file_hash
from .utils import is_hidden


def get_file_hash_map(files: list[Path]) -> dict[Path, str]:
    """Get hash map for multiple files.

    Args:
        files: List of file paths

    Returns:
        Mapping of file_path → hash (excludes non-existent files)
    """
    result: dict[Path, str] = {}
    for file_path in files:
        if file_path.exists():
            result[file_path] = compute_file_hash(file_path)
    return result


def is_hidden_file(file_path: Path) -> bool:
    """Check if a file name starts with a dot.

    Args:
        file_path: Path to check

    Returns:
        True if file name starts with '.'
    """
    return is_hidden(file_path)


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
            if is_hidden(part):
                return True
        return False
    except ValueError:
        return False


def get_auto_discover_candidates(
    base_dir: Path,
    exclude: Optional[list[Path | str]] = None,
) -> list[Path]:
    """Get files that should be auto-discovered (not hidden, not git-tracked).

    Args:
        base_dir: Directory to search in
        exclude: List of files and glob patterns to exclude

    Returns:
        List of files that are candidates for auto-discovery
    """
    def resolve_exclude(files: list[Path | str]) -> Generator[Path, None, None]:
        for f in files:
            if isinstance(f, Path):
                yield f
            else:
                for gf in base_dir.rglob(f):
                    yield gf

    if exclude is None:
        excluded_files: set[Path] = set()
    else:
        excluded_files = set(resolve_exclude(exclude))

    candidates: list[Path] = []

    for item in base_dir.rglob("*"):
        if item.is_file():
            if is_hidden_file(item):
                continue

            if is_in_hidden_directory(item, base_dir):
                continue

            if item in excluded_files:
                continue

            candidates.append(item)

    return candidates


def categorize_files_by_changes(
    before_hashes: dict[Path, str],
    after_hashes: dict[Path, str],
) -> list[Path]:
    """Categorize files as input/output based on hash changes.

    Args:
        before_hashes: File hashes before execution
        after_hashes: File hashes after execution

    Returns:
        Files with different hash OR created during execution
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

    return output_files