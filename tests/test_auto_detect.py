"""Tests for auto_detect.py."""

import subprocess
import tempfile
from pathlib import Path

from rair.auto_detect import (
    is_hidden_file,
    is_in_hidden_directory,
    get_auto_discover_candidates,
    compute_file_hash,
    get_file_hash_map,
    get_hidden_dirs,
    should_exclude_file,
    categorize_files_by_changes,
)


class TestIsHiddenFile:
    def test_hidden_file_returns_true(self):
        assert is_hidden_file(Path(".hidden_file"))

    def test_hidden_file_in_subdir_returns_true(self):
        assert is_hidden_file(Path("dir/.hidden"))

    def test_normal_file_returns_false(self):
        assert not is_hidden_file(Path("normal_file.txt"))

    def test_normal_file_in_subdir_returns_false(self):
        assert not is_hidden_file(Path("dir/file.txt"))


class TestIsInHiddenDirectory:
    def test_file_in_git_dir_returns_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            git_dir = tmpdir_path / ".git"
            git_dir.mkdir()
            file_path = git_dir / "config"
            file_path.touch()

        assert is_in_hidden_directory(file_path, tmpdir_path)

    def test_file_in_nested_hidden_returns_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            hidden_dir = tmpdir_path / ".cache"
            hidden_dir.mkdir()
            nested_dir = hidden_dir / "nested"
            nested_dir.mkdir()
            file_path = nested_dir / "file.txt"
            file_path.touch()

        assert is_in_hidden_directory(file_path, tmpdir_path)

    def test_file_in_normal_dir_returns_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            normal_dir = tmpdir_path / "data"
            normal_dir.mkdir()
            file_path = normal_dir / "file.txt"
            file_path.touch()

        assert not is_in_hidden_directory(file_path, tmpdir_path)

    def test_file_outside_base_dir_returns_false(self):
        tmpdir1 = Path(tempfile.mkdtemp())
        tmpdir2 = Path(tempfile.mkdtemp())

        file_path = tmpdir2 / "file.txt"
        file_path.touch()

        try:
            assert not is_in_hidden_directory(file_path, tmpdir1)
        finally:
            file_path.unlink()
            tmpdir2.rmdir()
            tmpdir1.rmdir()


class TestGetAutoDiscoverCandidates:
    def test_returns_non_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "normal.txt").write_text("content")
            (tmpdir_path / ".hidden").write_text("hidden")

            candidates = get_auto_discover_candidates(tmpdir_path, [])
            names = {f.name for f in candidates}
            assert "normal.txt" in names
            assert ".hidden" not in names

    def test_returns_non_git_tracked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tracked_file = tmpdir_path / "tracked.txt"
            tracked_file.write_text("tracked")
            untracked_file = tmpdir_path / "untracked.txt"
            untracked_file.write_text("untracked")

            candidates = get_auto_discover_candidates(tmpdir_path, [tracked_file])
            names = {f.name for f in candidates}
            assert "untracked.txt" in names
            assert "tracked.txt" not in names

    def test_excludes_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            hidden_dir = tmpdir_path / ".cache"
            hidden_dir.mkdir()
            (hidden_dir / "file.txt").write_text("hidden content")
            (tmpdir_path / "normal.txt").write_text("normal")

            candidates = get_auto_discover_candidates(tmpdir_path, [])
            names = {f.name for f in candidates}
            assert "normal.txt" in names
            assert "file.txt" not in names

    def test_empty_when_all_tracked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("1")
            file2 = tmpdir_path / "file2.txt"
            file2.write_text("2")

            candidates = get_auto_discover_candidates(tmpdir_path, [file1, file2])
            assert len(candidates) == 0


class TestComputeFileHash:
    def test_same_content_same_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "test.txt"
            file_path.write_text("same content")

            hash1 = compute_file_hash(file_path)
            hash2 = compute_file_hash(file_path)
            assert hash1 == hash2

    def test_different_content_different_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("content 1")
            file2 = tmpdir_path / "file2.txt"
            file2.write_text("content 2")

            hash1 = compute_file_hash(file1)
            hash2 = compute_file_hash(file2)
            assert hash1 != hash2

    def test_hash_length_20(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "test.txt"
            file_path.write_text("test")

            hash_val = compute_file_hash(file_path)
            assert len(hash_val) == 20
            assert hash_val.isalnum()

    def test_nonexistent_file_returns_empty(self):
        result = compute_file_hash(Path("/nonexistent/path"))
        assert result == ""


class TestGetFileHashMap:
    def test_returns_correct_mapping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("content 1")
            file2 = tmpdir_path / "file2.txt"
            file2.write_text("content 2")

            result = get_file_hash_map([file1, file2])
            assert file1 in result
            assert file2 in result
            assert result[file1] == compute_file_hash(file1)
            assert result[file2] == compute_file_hash(file2)

    def test_skips_nonexistent_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "exist.txt"
            file1.write_text("exists")
            file2 = tmpdir_path / "nonexist.txt"

            result = get_file_hash_map([file1, file2])
            assert file1 in result
            assert file2 not in result

    def test_empty_list_returns_empty(self):
        result = get_file_hash_map([])
        assert result == {}


class TestGetHiddenDirs:
    def test_finds_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "normal").mkdir()
            (tmpdir_path / ".git").mkdir()
            (tmpdir_path / ".cache").mkdir()

            result = get_hidden_dirs(tmpdir_path)
            names = {p.name for p in result}
            assert ".git" in names
            assert ".cache" in names
            assert "normal" not in names

    def test_finds_nested_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            level1 = tmpdir_path / ".cache"
            level1.mkdir()
            level2 = level1 / ".nested"
            level2.mkdir()

            result = get_hidden_dirs(tmpdir_path)
            paths = {p for p in result}
            assert level1 in paths
            assert level2 in paths

    def test_excludes_normal_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "data").mkdir()
            (tmpdir_path / "results").mkdir()

            result = get_hidden_dirs(tmpdir_path)
            assert len(result) == 0


class TestShouldExcludeFile:
    def test_excludes_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / ".hidden"
            file_path.write_text("content")

        assert should_exclude_file(file_path, tmpdir_path, tmpdir_path / "archive", set(), None)

    def test_excludes_files_in_hidden_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            hidden_dir = tmpdir_path / ".cache"
            hidden_dir.mkdir()
            file_path = hidden_dir / "file.txt"
            file_path.write_text("content")

        assert should_exclude_file(file_path, tmpdir_path, tmpdir_path / "archive", set(), None)

    def test_excludes_git_tracked_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "tracked.txt"
            file_path.write_text("tracked")

        assert should_exclude_file(file_path, tmpdir_path, tmpdir_path / "archive", set(), [file_path])

    def test_excludes_archive_dir_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            archive_dir = tmpdir_path / "rairarchive"
            archive_dir.mkdir()
            file_path = archive_dir / "data.txt"
            file_path.write_text("data")

        assert should_exclude_file(file_path, tmpdir_path, archive_dir, set(), None)

    def test_allows_eligible_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file_path = tmpdir_path / "normal.txt"
            file_path.write_text("normal content")

        assert not should_exclude_file(file_path, tmpdir_path, tmpdir_path / "archive", set(), None)


class TestCategorizeFilesByChanges:
    def test_unchanged_files_as_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("same content")

        file_hash = compute_file_hash(file1)

        before = {file1: file_hash}
        after = {file1: file_hash}

        input_files, output_files = categorize_files_by_changes(before, after)
        assert file1 in input_files
        assert file1 not in output_files

    def test_changed_files_as_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("old content")
            old_hash = compute_file_hash(file1)
            file1.write_text("new content")
            new_hash = compute_file_hash(file1)

        before = {file1: old_hash}
        after = {file1: new_hash}

        input_files, output_files = categorize_files_by_changes(before, after)
        assert file1 not in input_files
        assert file1 in output_files

    def test_created_files_as_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("content")

        before: dict = {}
        after = {file1: compute_file_hash(file1)}

        input_files, output_files = categorize_files_by_changes(before, after)
        assert file1 in output_files
        assert file1 not in input_files

    def test_deleted_files_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file1.write_text("content")

        before = {file1: compute_file_hash(file1)}
        after: dict = {}

        input_files, output_files = categorize_files_by_changes(before, after)
        assert file1 not in input_files
        assert file1 not in output_files

    def test_mixed_scenario(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            unchanged = tmpdir_path / "unchanged.txt"
            unchanged.write_text("same")
            unchanged_hash = compute_file_hash(unchanged)

            changed = tmpdir_path / "changed.txt"
            changed.write_text("old")
            changed_hash_old = compute_file_hash(changed)
            changed.write_text("new")
            changed_hash_new = compute_file_hash(changed)

            created = tmpdir_path / "created.txt"
            created.write_text("new file")

        deleted_path = tmpdir_path / "deleted.txt"
        deleted_hash = "deleted_hash"

        before = {
            unchanged: unchanged_hash,
            changed: changed_hash_old,
            deleted_path: deleted_hash,
        }
        after = {
            unchanged: unchanged_hash,
            changed: changed_hash_new,
            created: compute_file_hash(created),
        }

        input_files, output_files = categorize_files_by_changes(before, after)

        assert unchanged in input_files
        assert unchanged not in output_files

        assert changed in output_files
        assert changed not in input_files

        assert created in output_files
        assert created not in input_files

        assert deleted_path not in input_files
        assert deleted_path not in output_files