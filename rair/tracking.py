"""File tracking and caching for rair."""

import hashlib
import json
from pathlib import Path
from typing import Optional
from .hashing import compute_file_hash
from .models import FileSnapshot, TrackedFile


def get_mtime(path: Path) -> float:
    """Get the modification time of a file."""
    return path.stat().st_mtime


def discover_files(
    base_dir: Path,
    include_globs: list[str],
    exclude_globs: list[str],
) -> list[Path]:
    """Discover files matching the given globs, excluding specified patterns."""
    from fnmatch import fnmatch

    files: set[Path] = set()

    if not include_globs:
        return []

    for glob_pattern in include_globs:
        matches = base_dir.glob(glob_pattern)
        for match in matches:
            if match.is_file():
                relative_path = match.relative_to(base_dir)
                path_str = str(relative_path)

                excluded = False
                for exclude_pattern in exclude_globs:
                    if fnmatch(path_str, exclude_pattern) or fnmatch(
                        match.name, exclude_pattern
                    ):
                        excluded = True
                        break

                if not excluded:
                    files.add(match)

    return sorted(files)


def create_snapshot(files: list[Path], cache: dict[str, tuple[str, float]]) -> FileSnapshot:
    """Create a snapshot of files, using cached hashes when possible."""
    tracked_files: dict[str, TrackedFile] = {}

    for file_path in files:
        path_str = str(file_path)
        current_mtime = get_mtime(file_path)

        cached_hash: Optional[str] = None
        cached_mtime: Optional[float] = None

        if path_str in cache:
            cached_hash, cached_mtime = cache[path_str]

        if cached_hash is not None and cached_mtime == current_mtime:
            hash_val = cached_hash
        else:
            hash_val = compute_file_hash(file_path)
            cache[path_str] = (hash_val, current_mtime)

        tracked_files[path_str] = TrackedFile(
            path=file_path,
            hash=hash_val,
            mtime=current_mtime,
        )

    return FileSnapshot(files=tracked_files)


def load_cache(cache_dir: Path) -> dict[str, tuple[str, float]]:
    """Load the file hash cache from disk."""
    cache_file = cache_dir / "file_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
                return {k: tuple(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_cache(cache_dir: Path, cache: dict[str, tuple[str, float]]) -> None:
    """Save the file hash cache to disk."""
    cache_file = cache_dir / "file_cache.json"
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump({k: list(v) for k, v in cache.items()}, f)