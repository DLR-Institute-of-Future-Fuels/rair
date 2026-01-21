"""Tests for run.json generation."""

import json
import tempfile
from pathlib import Path
import pytest

from rair.archive import (
    write_run_json,
    _make_relative_path,
    _format_file_for_json,
)
from rair.models import GitInfo, TrackedFile


class TestMakeRelativePath:
    def test_relative_when_in_project(self):
        project_dir = Path("/project")
        archive_dir = Path("/project/archive")
        path = Path("/project/data/file.txt")

        result = _make_relative_path(project_dir, archive_dir, path)
        assert result == Path("data/file.txt")

    def test_absolute_when_outside_project(self):
        project_dir = Path("/project")
        archive_dir = Path("/other/archive")
        path = Path("/project/data/file.txt")

        result = _make_relative_path(project_dir, archive_dir, path)
        assert result == Path("/project/data/file.txt")

    def test_relative_when_archive_is_subdir(self):
        project_dir = Path("/project")
        archive_dir = Path("/project/.rairarchive")
        path = Path("/project/data/file.txt")

        result = _make_relative_path(project_dir, archive_dir, path)
        assert result == Path("data/file.txt")


class TestFormatFileForJson:
    def test_format_with_archived_path(self):
        project_dir = Path("/project")
        archive_dir = Path("/project/archive")
        tracked = TrackedFile(Path("/project/data/input.txt"), "hash1234", 1.0)
        archived = Path("/project/archive/data/hash1234_input.txt")

        result = _format_file_for_json(project_dir, archive_dir, tracked, archived)

        assert str(result["path"]).replace("\\", "/") == "data/input.txt"
        assert result["hash"] == "hash1234"
        assert result["hash_prefix"] == "hash1234"
        assert str(result["archived_path"]).replace("\\", "/") == "archive/data/hash1234_input.txt"

    def test_format_without_archived_path(self):
        project_dir = Path("/project")
        archive_dir = Path("/project/archive")
        tracked = TrackedFile(Path("/project/data/input.txt"), "hash1234", 1.0)
        archived = None

        result = _format_file_for_json(project_dir, archive_dir, tracked, archived)

        assert str(result["path"]).replace("\\", "/") == "data/input.txt"
        assert result["hash"] == "hash1234"
        assert result["hash_prefix"] == "hash1234"
        assert result["archived_path"] is None


class TestWriteRunJson:
    def test_json_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            project_dir = Path(tmpdir)
            archive_dir = project_dir / "archive"
            archive_dir.mkdir()

            git_info = GitInfo(
                commit_hash="abc123def456",
                short_hash="abc123d",
                branch="main",
                diff="",
                diff_hash="",
                tracking_url="https://github.com/user/repo",
            )
            input_files = [
                TrackedFile(Path("data/input.txt"), "hash1", 1.0),
            ]
            output_files = [
                TrackedFile(Path("results/output.txt"), "hash2", 2.0),
            ]
            archived_files = {
                str(Path("data/input.txt")): archive_dir / "data" / "hash1_input.txt",
                str(Path("results/output.txt")): archive_dir / "data" / "hash2_output.txt",
            }

            write_run_json(
                run_dir,
                Path("script.py"),
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
            )

            json_path = run_dir / "run.json"
            assert json_path.exists()

            with open(json_path) as f:
                data = json.load(f)

            assert "run_id" in data
            assert "run_timestamp" in data
            assert "script" in data
            assert "git" in data
            assert "input_files" in data
            assert "output_files" in data

            assert data["script"] == "script.py"
            assert data["git"]["commit_hash"] == "abc123def456"
            assert data["git"]["short_hash"] == "abc123d"
            assert data["git"]["has_diff"] is False

    def test_json_with_diff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            project_dir = Path(tmpdir)
            archive_dir = project_dir / "archive"
            archive_dir.mkdir()

            git_info = GitInfo(
                commit_hash="abc123def456",
                short_hash="abc123d",
                branch="main",
                diff="some diff content",
                diff_hash="diff1234",
                tracking_url="https://github.com/user/repo",
            )
            input_files = []
            output_files = []
            archived_files = {}

            write_run_json(
                run_dir,
                Path("script.py"),
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
            )

            with open(run_dir / "run.json") as f:
                data = json.load(f)

            assert data["git"]["has_diff"] is True
            assert data["git"]["diff_hash"] == "diff1234"

    def test_json_file_entries(self):
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
                TrackedFile(Path("data/input.txt"), "hash1", 1.0),
                TrackedFile(Path("data/config.json"), "hash2", 1.0),
            ]
            output_files = [
                TrackedFile(Path("results/output.txt"), "hash3", 2.0),
            ]
            archived_files = {
                str(Path("data/input.txt")): archive_dir / "data" / "hash1_input.txt",
                str(Path("data/config.json")): archive_dir / "data" / "hash2_config.json",
                str(Path("results/output.txt")): archive_dir / "data" / "hash3_output.txt",
            }

            write_run_json(
                run_dir,
                Path("script.py"),
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
            )

            with open(run_dir / "run.json") as f:
                data = json.load(f)

            assert len(data["input_files"]) == 2
            assert len(data["output_files"]) == 1

            paths = [str(p["path"]).replace("\\", "/") for p in data["input_files"]]
            assert "data/config.json" in paths
            assert "data/input.txt" in paths
            assert str(data["output_files"][0]["path"]).replace("\\", "/") == "results/output.txt"

    def test_absolute_paths_when_archive_outside_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()
            archive_dir = Path(tmpdir) / "archive"
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
                TrackedFile(project_dir / "data/input.txt", "hash1", 1.0),
            ]
            output_files = []
            archived_files = {
                str(project_dir / "data/input.txt"): archive_dir / "data" / "hash1_input.txt",
            }

            write_run_json(
                run_dir,
                project_dir / "script.py",
                project_dir,
                archive_dir,
                git_info,
                input_files,
                output_files,
                archived_files,
            )

            with open(run_dir / "run.json") as f:
                data = json.load(f)

            assert data["script"] == str(project_dir / "script.py")
            assert data["input_files"][0]["path"] == str(project_dir / "data/input.txt")
            assert data["input_files"][0]["archived_path"] == str(archive_dir / "data" / "hash1_input.txt")