"""Data models for rair."""

from dataclasses import dataclass
from pathlib import Path


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
class FileSnapshot:
    """A snapshot of tracked files at a point in time."""

    files: dict[str, TrackedFile]

    def get_changed(self, other: "FileSnapshot") -> list[str]:
        changed: list[str] = []
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
