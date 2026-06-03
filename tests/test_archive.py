"""Tests for archive.py."""

import tempfile
from pathlib import Path

from rair.archive import (
    compute_file_hash,
    get_unique_data_path,
    copy_to_data_archive,
    generate_run_id,
    create_run_directory,
    get_gitlab_link,
    write_run_info,
    compress_diff,
)
from rair.models import GitInfo, TrackedFile


class TestComputeFileHash:
    def test_hash_content(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            path = Path(f.name)

        try:
            hash1 = compute_file_hash(path)
            assert len(hash1) == 20
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

            run_id1 = generate_run_id(archive_dir, "abc123de")
            run_id2 = generate_run_id(archive_dir, "def456gh")
            run_id3 = generate_run_id(archive_dir, "ghi789ij")

            assert run_id1.endswith("-001-abc123de")
            assert run_id2.endswith("-002-def456gh")
            assert run_id3.endswith("-003-ghi789ij")


def test_date_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir) / "archive"
        archive_dir.mkdir()

        run_id = generate_run_id(archive_dir, "hash123")
        import datetime
        today = datetime.datetime.now().strftime("%Y%m%d")
        assert run_id.startswith(today)
        assert "-" in run_id
        assert "-hash123" in run_id


def test_new_day_resets():
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir) / "archive"
        archive_dir.mkdir()

        run_id1 = generate_run_id(archive_dir, "hash1")
        assert run_id1.endswith("-001-hash1")

        run_id2 = generate_run_id(archive_dir, "hash2")
        assert run_id2.endswith("-002-hash2")


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

            from rair.archive import compute_combined_hash
            combined_hash, _ = compute_combined_hash(
                "abc123",
                "",
                [f.hash for f in input_files],
            )

            write_run_info(
                run_dir,
                ["script.py"],
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
                combined_hash,
                execution_time=0.0,
                comment="",
            )

            info_path = run_dir / "info.md"
            assert info_path.exists()
            content = info_path.read_text()
            assert "abc123" in content
            assert "input.txt" in content
            assert "output.txt" in content
            assert "->" in content

    def test_write_info_with_comment(self):
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
            input_files: list[TrackedFile] = []
            output_files: list[TrackedFile] = []
            archived_files: dict[str, Path] = {}

            from rair.archive import compute_combined_hash
            combined_hash, _ = compute_combined_hash("abc123", "", [])

            write_run_info(
                run_dir,
                ["script.py"],
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
                combined_hash,
                execution_time=0.0,
                comment="Test comment for this run",
            )

            info_path = run_dir / "info.md"
            assert info_path.exists()
            content = info_path.read_text()
            assert "Comment: Test comment for this run" in content


class TestCompressDiff:
    def test_compress_diff_empty(self):
        result = compress_diff("")
        assert result == ""

    def test_compress_diff_simple_file_change(self):
        diff = """diff --git a/model.py b/model.py
+++ b/model.py
@@ -5,3 +5,3 @@
 learning_rate = 0.001
-epochs = 10
+epochs = 15"""
        result = compress_diff(diff)
        assert "diff --git" not in result
        assert "epochs = 15" in result
        assert "learning_rate = 0.001" not in result

    def test_compress_diff_parameter_changes(self):
        diff = """diff --git a/config.py b/config.py
+++ b/config.py
@@ -10,5 +10,5 @@
 batch_size = 32
-learning_rate = 0.001
+learning_rate = 0.01
-dropout = 0.5
+dropout = 0.3"""
        result = compress_diff(diff)
        assert "learning_rate = 0.01" in result
        assert "dropout = 0.3" in result
        assert "batch_size = 32" not in result

    def test_compress_diff_no_parameters(self):
        diff = """diff --git a/README.md b/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 Hello world
+
+New section
 Another line"""
        result = compress_diff(diff)
        lines = result.split('\n')
        parameter_lines = [l for l in lines if not l.startswith('+') and '=' in l]
        assert len(parameter_lines) == 0

    def test_compress_diff_multiple_files(self):
        diff = """diff --git a/model.py b/model.py
--- a/model.py
+++ b/model.py
@@ -5,0 +5,1 @@
+param = value

diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -10,0 +10,1 @@
+setting = enabled"""
        result = compress_diff(diff)
        assert "param = value" in result
        assert "setting = enabled" in result

    def test_compress_diff_arithmetic_expressions(self):
        diff = """diff --git a/config.py b/config.py
+++ b/config.py
@@ -10,5 +10,5 @@
-learning_rate = base_lr * 0.1
+learning_rate = base_lr * 0.05
-epochs = 100
+epochs = 150
-alpha = beta
+alpha = beta + 2"""
        result = compress_diff(diff)
        assert "learning_rate = base_lr * 0.05" in result
        assert "epochs = 150" in result
        assert "alpha = beta + 2" in result


class TestOutputHardlinksInRun:
    def test_creates_hardlinks_in_run_folder(self):
        from rair.archive import create_output_hardlinks_in_run
        from rair.models import FileSnapshot, TrackedFile

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "runs" / "test_run"
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()
            run_dir.mkdir(parents=True)

            source_file = data_dir / "abc123_output.txt"
            source_file.write_text("test content")
            mtime = source_file.stat().st_mtime

            snapshot = FileSnapshot(files={})
            tracked_file = TrackedFile(path=Path("output.txt"), hash="abc123", mtime=mtime)
            snapshot.files["output.txt"] = tracked_file

            archived_paths = {"output.txt": source_file}

            create_output_hardlinks_in_run(snapshot, run_dir, archived_paths)

            hardlink_path = run_dir / "output.txt"
            assert hardlink_path.exists()
            assert hardlink_path.stat().st_ino == source_file.stat().st_ino

    def test_hardlink_skips_existing_files(self):
        from rair.archive import create_output_hardlinks_in_run
        from rair.models import FileSnapshot, TrackedFile

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "runs" / "test_run"
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()
            run_dir.mkdir(parents=True)

            source_file = data_dir / "abc123_output.txt"
            source_file.write_text("test content")
            mtime = source_file.stat().st_mtime

            existing_file = run_dir / "output.txt"
            existing_file.write_text("existing content")

            snapshot = FileSnapshot(files={})
            tracked_file = TrackedFile(path=Path("output.txt"), hash="abc123", mtime=mtime)
            snapshot.files["output.txt"] = tracked_file

            archived_paths = {"output.txt": source_file}

            create_output_hardlinks_in_run(snapshot, run_dir, archived_paths)

            assert existing_file.read_text() == "existing content"

    def test_handles_empty_snapshot(self):
        from rair.archive import create_output_hardlinks_in_run
        from rair.models import FileSnapshot

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "runs" / "test_run"
            run_dir.mkdir(parents=True)

            snapshot = FileSnapshot(files={})
            archived_paths = {}

            create_output_hardlinks_in_run(snapshot, run_dir, archived_paths)

            assert run_dir.exists()