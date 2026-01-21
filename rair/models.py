"""Data models for rair."""

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class TrackedFile:
    """Represents a file being tracked by rair."""

    path: Path
    hash: str
    mtime: float

    @property
    def hash_prefix(self) -> str:
        return self.hash[:8]

    def matches(self, other: "TrackedFile") -> bool:
        return self.hash == other.hash


@dataclass
class RunConfig:
    """Configuration for a single rair run.

    .. deprecated::
        Use :class:`rair.config.RairConfig` instead.
        The RunConfig will be removed in a future version.
    """

    input_globs: list[str] = field(default_factory=list)
    output_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)
    archive_dir: Path = Path("rairarchive")

    def __post_init__(self) -> None:
        warnings.warn(
            "RunConfig is deprecated. Use RairConfig from rair.config instead.",
            DeprecationWarning,
            stacklevel=2,
        )


@dataclass
class FileSnapshot:
    """A snapshot of tracked files at a point in time."""

    files: dict[str, TrackedFile]

    def get_changed(self, other: "FileSnapshot") -> list[str]:
        changed = []
        for path, current in self.files.items():
            if path not in other.files:
                changed.append(path)
            elif not current.matches(other.files[path]):
                changed.append(path)
        return changed

    def get_added(self, other: "FileSnapshot") -> list[str]:
        return [p for p in other.files if p not in self.files]

    def get_removed(self, other: "FileSnapshot") -> list[str]:
        return [p for p in self.files if p not in other.files]


@dataclass
class GitInfo:
    """Git state information for a run."""

    commit_hash: str
    short_hash: str
    branch: str
    diff: str
    diff_hash: str
    tracking_url: str


@dataclass
class RunInfo:
    """Metadata for a completed run."""

    run_id: str
    git_info: GitInfo
    script: Path
    archive_dir: Path
    run_timestamp: str
    input_files: list[str]
    output_files: list[str]