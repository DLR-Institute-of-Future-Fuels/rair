"""Tests for tracking.py."""

import tempfile
from pathlib import Path
from rair.tracking import (
    compute_file_hash,
    discover_files,
    create_snapshot,
    load_cache,
    save_cache,
)


class TestComputeFileHash:
    def test_hash_content(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)

        try:
            hash1 = compute_file_hash(path)
            assert len(hash1) == 20
            assert hash1.isalnum()

            hash2 = compute_file_hash(path)
            assert hash1 == hash2
        finally:
            path.unlink()

    def test_different_content(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content 1")
            f.flush()
            path1 = Path(f.name)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content 2")
            f.flush()
            path2 = Path(f.name)

        try:
            hash1 = compute_file_hash(path1)
            hash2 = compute_file_hash(path2)
            assert hash1 != hash2
        finally:
            path1.unlink()
            path2.unlink()


class TestDiscoverFiles:
    def test_simple_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            (dir_path / "file1.txt").write_text("a")
            (dir_path / "file2.txt").write_text("b")
            (dir_path / "subdir").mkdir()
            (dir_path / "subdir" / "file3.txt").write_text("c")

            files = discover_files(dir_path, ["*.txt"], [])
            names = {f.name for f in files}
            assert names == {"file1.txt", "file2.txt"}

    def test_recursive_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            (dir_path / "file1.txt").write_text("a")
            (dir_path / "subdir").mkdir()
            (dir_path / "subdir" / "file2.txt").write_text("b")

            files = discover_files(dir_path, ["**/*.txt"], [])
            names = {f.name for f in files}
            assert names == {"file1.txt", "file2.txt"}

    def test_exclude_pattern(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            (dir_path / "data.txt").write_text("data")
            (dir_path / "result.txt").write_text("result")
            (dir_path / "exclude.txt").write_text("excluded")

            files = discover_files(dir_path, ["*.txt"], ["exclude.txt"])
            names = {f.name for f in files}
            assert names == {"data.txt", "result.txt"}


class TestCreateSnapshot:
    def test_snapshot_with_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            (dir_path / "test.txt").write_text("content")
            path = dir_path / "test.txt"

            cache: dict[str, tuple[str, float]] = {}
            snapshot1 = create_snapshot([path], cache)
            assert len(snapshot1.files) == 1

            snapshot2 = create_snapshot([path], cache)
            assert len(snapshot2.files) == 1

            assert snapshot1.files[str(path)].hash == snapshot2.files[str(path)].hash


class TestLoadSaveCache:
    def test_load_and_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_data = {
                "file1.txt": ("hash1", 1234567890.0),
                "file2.txt": ("hash2", 1234567891.0),
            }

            save_cache(cache_dir, cache_data)
            loaded = load_cache(cache_dir)

            assert loaded["file1.txt"] == ("hash1", 1234567890.0)
            assert loaded["file2.txt"] == ("hash2", 1234567891.0)

    def test_load_empty_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            loaded = load_cache(cache_dir)
            assert loaded == {}

    def test_load_corrupted_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "file_cache.json").write_text("{invalid json}")

            loaded = load_cache(cache_dir)
            assert loaded == {}