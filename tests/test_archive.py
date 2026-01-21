"""Tests for archive.py."""

import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from rair.archive import (
    compute_file_hash,
    get_unique_data_path,
    copy_to_data_archive,
    generate_run_id,
    create_run_directory,
    get_gitlab_link,
    write_run_info,
    archive_files,
)
from rair.models import FileSnapshot, GitInfo, TrackedFile


class TestComputeFileHash:
    def test_hash_content(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)

        try:
            hash1 = compute_file_hash(path)
            assert len(hash1) == 64
        finally:
            path.unlink()


class TestGetUniqueDataPath:
    def test_unique_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            path = get_unique_data_path(data_dir, "abc123", "myfile.txt")

            assert path.parent == data_dir
            assert path.name.startswith("abc123_")


class TestCopyToDataArchive:
    def test_copy_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            data_dir = Path(tmpdir) / "data"
            src_dir.mkdir()
            (src_dir / "test.txt").write_text("content")

            dest = copy_to_data_archive(src_dir / "test.txt", data_dir)

            assert dest.exists()
            assert dest.read_text() == "content"

    def test_deduplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "src"
            data_dir = Path(tmpdir) / "data"
            src_dir.mkdir()

            file_path = src_dir / "data.txt"
            file_path.write_text("same content")

            dest1 = copy_to_data_archive(file_path, data_dir)
            dest2 = copy_to_data_archive(file_path, data_dir)

            assert dest1 == dest2


class TestGenerateRunId:
    def test_increments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_dir = Path(tmpdir) / "archive"
            archive_dir.mkdir()

            run_id1 = generate_run_id(archive_dir)
            run_id2 = generate_run_id(archive_dir)
            run_id3 = generate_run_id(archive_dir)

            assert run_id1.endswith("-001")
            assert run_id2.endswith("-002")
            assert run_id3.endswith("-003")

    def test_date_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_dir = Path(tmpdir) / "archive"
            archive_dir.mkdir()

            run_id = generate_run_id(archive_dir)
            import datetime
            today = datetime.datetime.now().strftime("%Y%m%d")
            assert run_id.startswith(today)
            assert "-" in run_id

    def test_new_day_resets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_dir = Path(tmpdir) / "archive"
            archive_dir.mkdir()

            run_id1 = generate_run_id(archive_dir)
            assert run_id1.endswith("-001")

            run_id2 = generate_run_id(archive_dir)
            assert run_id2.endswith("-002")


class TestCreateRunDirectory:
    def test_create_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_dir = Path(tmpdir) / "archive"
            run_dir = create_run_directory(archive_dir, "test_run")

            assert run_dir.exists()
            assert run_dir.is_dir()


class TestGetGitlabLink:
    def test_gitlab_url(self):
        link = get_gitlab_link(
            "https://gitlab.dlr.de/user/repo.git",
            "abc123def",
        )
        assert link == "https://gitlab.dlr.de/user/repo/-/tree/abc123def"

    def test_other_url(self):
        link = get_gitlab_link("https://github.com/user/repo.git", "abc123")
        assert link is None


class TestWriteRunInfo:
    def test_write_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            project_dir = Path(tmpdir)
            archive_dir = project_dir / "archive"
            archive_dir.mkdir()
            git_info = GitInfo(
                commit_hash="abc123",
                short_hash="abc",
                branch="main",
                diff="",
                diff_hash="",
                tracking_url="https://github.com",
            )
            input_files = [
                TrackedFile(Path("input.txt"), "hash1", 1.0),
            ]
            output_files = [
                TrackedFile(Path("output.txt"), "hash2", 2.0),
            ]
            archived_files = {
                str(Path("input.txt")): Path(tmpdir) / "data" / "hash1_input.txt",
                str(Path("output.txt")): Path(tmpdir) / "data" / "hash2_output.txt",
            }

            write_run_info(
                run_dir,
                Path("script.py"),
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
            )

            info_path = run_dir / "info.md"
            assert info_path.exists()
            content = info_path.read_text()
            assert "abc123" in content
            assert "input.txt" in content
            assert "output.txt" in content
            assert "->" in content


class TestArchiveFiles:
    def test_archive_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()
            (src_dir / "file.txt").write_text("content")

            snapshot = FileSnapshot(
                files={
                    str(src_dir / "file.txt"): TrackedFile(
                        src_dir / "file.txt", "hash123", 1.0
                    )
                }
            )

            archived = archive_files(snapshot, data_dir)

            assert len(archived) == 1
            assert list(archived.values())[0].exists()