"""Tests for models.py."""
from pathlib import Path

from rair.models import FileSnapshot, GitInfo, TrackedFile
from rair.config import RairConfig


class TestTrackedFile:
    def test_hash_prefix(self):
        tracked = TrackedFile(
            path=Path("test.txt"),
            hash="abcd1234efgh5678",
            mtime=1234567890.0,
        )
        assert tracked.hash_prefix == "abcd1234"

    def test_matches_identical(self):
        tracked1 = TrackedFile(
            path=Path("test.txt"),
            hash="abcd1234efgh5678",
            mtime=1234567890.0,
        )
        tracked2 = TrackedFile(
            path=Path("test.txt"),
            hash="abcd1234efgh5678",
            mtime=1234567890.0,
        )
        assert tracked1.matches(tracked2)

    def test_matches_different_hash(self):
        tracked1 = TrackedFile(
            path=Path("test.txt"),
            hash="abcd1234efgh5678",
            mtime=1234567890.0,
        )
        tracked2 = TrackedFile(
            path=Path("test.txt"),
            hash="differenthash1234",
            mtime=1234567890.0,
        )
        assert not tracked1.matches(tracked2)


class TestRairConfig:
    def test_default_values(self):
        config = RairConfig()
        assert config.input_glob == []
        assert config.output_glob == []
        assert config.exclude_glob == []
        assert config.archive_dir == Path("rairarchive")

    def test_custom_values(self):
        config = RairConfig(
            input_glob=["data/*.csv"],
            output_glob=["results/*.txt"],
            exclude_glob=["*.tmp"],
            archive_dir=Path("my_archive"),
        )
        assert config.input_glob == ["data/*.csv"]
        assert config.output_glob == ["results/*.txt"]
        assert config.exclude_glob == ["*.tmp"]
        assert config.archive_dir == Path("my_archive")


class TestFileSnapshot:
    def test_get_changed(self):
        before = FileSnapshot(
            files={
                "a.txt": TrackedFile(Path("a.txt"), "hash1", 1.0),
                "b.txt": TrackedFile(Path("b.txt"), "hash2", 1.0),
            }
        )
        after = FileSnapshot(
            files={
                "a.txt": TrackedFile(Path("a.txt"), "hash1_changed", 1.0),
                "b.txt": TrackedFile(Path("b.txt"), "hash2", 1.0),
            }
        )
        changed = before.get_changed(after)
        assert changed == ["a.txt"]

    def test_get_added(self):
        before = FileSnapshot(
            files={
                "a.txt": TrackedFile(Path("a.txt"), "hash1", 1.0),
            }
        )
        after = FileSnapshot(
            files={
                "a.txt": TrackedFile(Path("a.txt"), "hash1", 1.0),
                "b.txt": TrackedFile(Path("b.txt"), "hash2", 1.0),
            }
        )
        added = before.get_added(after)
        assert added == ["b.txt"]

    def test_get_removed(self):
        before = FileSnapshot(
            files={
                "a.txt": TrackedFile(Path("a.txt"), "hash1", 1.0),
                "b.txt": TrackedFile(Path("b.txt"), "hash2", 1.0),
            }
        )
        after = FileSnapshot(
            files={
                "a.txt": TrackedFile(Path("a.txt"), "hash1", 1.0),
            }
        )
        removed = before.get_removed(after)
        assert removed == ["b.txt"]


class TestGitInfo:
    def test_create_git_info(self):
        info = GitInfo(
            commit_hash="abc123",
            short_hash="abc",
            branch="main",
            diff="diff content",
            diff_hash="def456",
            tracking_url="https://github.com/user/repo",
        )
        assert info.commit_hash == "abc123"
        assert info.short_hash == "abc"
        assert info.branch == "main"