"""Tests for utils.py."""

import json
import tempfile
from pathlib import Path

from rair.utils import (
    safe_load_json,
    safe_write_json,
    ensure_directory,
    is_hidden,
    hash_to_short,
    HASH_LENGTH,
)


class TestSafeLoadJson:
    def test_loads_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "test.json"
            file_path.write_text('{"key": "value"}')

            result = safe_load_json(file_path)
            assert result == {"key": "value"}

    def test_returns_default_if_file_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "nonexistent.json"

            result = safe_load_json(file_path, {"default": True})
            assert result == {"default": True}

    def test_returns_default_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "invalid.json"
            file_path.write_text("{not valid json}")

            result = safe_load_json(file_path, {"default": "value"})
            assert result == {"default": "value"}

    def test_returns_none_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "nonexistent.json"

            result = safe_load_json(file_path)
            assert result is None


class TestSafeWriteJson:
    def test_writes_json_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "test.json"
            data = {"key": "value"}

            safe_write_json(file_path, data)

            assert file_path.exists()
            assert safe_load_json(file_path) == data

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "subdir" / "test.json"
            data = {"key": "value"}

            safe_write_json(file_path, data, create_dirs=True)

            assert file_path.exists()
            assert file_path.parent.exists()

    def test_no_create_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "test.json"
            data = {"key": "value"}

            safe_write_json(file_path, data, create_dirs=False)

            assert file_path.exists()


class TestEnsureDirectory:
    def test_creates_new_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            new_dir = tmpdir_path / "new_dir"

            result = ensure_directory(new_dir)

            assert result == new_dir
            assert new_dir.exists()

    def test_creates_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            nested_dir = tmpdir_path / "level1" / "level2" / "level3"

            result = ensure_directory(nested_dir)

            assert result == nested_dir
            assert nested_dir.exists()

    def test_handles_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            existing_dir = tmpdir_path / "existing"
            existing_dir.mkdir()

            result = ensure_directory(existing_dir)

            assert result == existing_dir
            assert existing_dir.exists()


class TestIsHidden:
    def test_path_starting_with_dot(self):
        assert is_hidden(Path(".hidden"))

    def test_string_starting_with_dot(self):
        assert is_hidden(".secret")

    def test_path_normal(self):
        assert not is_hidden(Path("normal.txt"))

    def test_string_normal(self):
        assert not is_hidden("file.txt")


class TestHashToShort:
    def test_truncates_to_hash_length(self):
        full_hash = "a" * 50
        result = hash_to_short(full_hash)
        assert len(result) == HASH_LENGTH
        assert result == "a" * HASH_LENGTH

    def test_shorter_hash(self):
        short_hash = "abc"
        result = hash_to_short(short_hash)
        assert result == "abc"

    def test_empty(self):
        result = hash_to_short("")
        assert result == ""