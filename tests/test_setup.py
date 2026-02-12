"""Tests for rair setup functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from rair.setup import (
    setup_interactive,
    write_config_to_file,
    is_git_project,
    read_gitignore,
    add_gitignore_entries,
)
from rair.config import RairConfig


class TestWriteConfigToFile:
    def test_write_config_creates_rair_toml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".rair.toml"
            config = RairConfig(
                archive_dir=Path("my_archive"),
                input_glob=["data/*.csv"],
                output_glob=["results/*.json"],
                exclude_glob=["*.tmp"],
                auto_discover=False,
            )

            write_config_to_file(config, config_path)

            assert config_path.exists()
            content = config_path.read_text()
            assert "[rair]" in content
            assert 'archive_dir = "my_archive"' in content
            assert 'input = "data/*.csv"' in content
            assert 'output = "results/*.json"' in content
            assert 'exclude = "*.tmp"' in content
            assert "auto_discover = false" in content

    def test_write_config_includes_default_command_and_output_files_in_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".rair.toml"
            config = RairConfig(
                archive_dir=Path("my_archive"),
                input_glob=["data/*.csv"],
                output_glob=["results/*.json"],
                exclude_glob=["*.tmp"],
                auto_discover=False,
                output_files_in_run=True,
                default_command="make",
            )

            write_config_to_file(config, config_path)

            assert config_path.exists()
            content = config_path.read_text()
            assert "[rair]" in content
            assert 'default_command = "make"' in content
            assert "output_files_in_run = true" in content

    def test_write_config_skips_none_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".rair.toml"
            config = RairConfig(
                archive_dir=Path("archive"),
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                auto_discover=True,
                default_command=None,
            )

            write_config_to_file(config, config_path)

            assert config_path.exists()
            content = config_path.read_text()
            assert "[rair]" in content
            assert "default_command" not in content
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".rair.toml"
            config = RairConfig(
                archive_dir=Path("archive"),
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                auto_discover=True,
            )

            write_config_to_file(config, config_path)

            assert config_path.exists()
            content = config_path.read_text()
            assert "[rair]" in content


class TestSetupInteractive:
    @patch("rair.setup.get_toplevel")
    @patch("rair.setup.is_git_project")
    @patch("rair.setup.Path.cwd")
    def test_setup_in_project_root_saves_to_project(self, mock_cwd, mock_is_git, mock_get_toplevel):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subdir = project_dir / "subdir"
            subdir.mkdir()

            mock_cwd.return_value = project_dir
            mock_get_toplevel.return_value = project_dir
            mock_is_git.return_value = False

            result = setup_interactive(
                archive_dir="test_archive",
                input_patterns="data/*.csv",
                output_patterns="results/*.json",
                auto_discover=True,
                output_files_in_run=False,
                default_command="",
                config_location="project",
            )

            assert result.archive_dir == Path("test_archive")
            assert result.input_glob == ["data/*.csv"]
            assert result.output_glob == ["results/*.json"]

            config_path = project_dir / ".rair.toml"
            assert config_path.exists()

    @patch("rair.setup.get_toplevel")
    @patch("rair.setup.is_git_project")
    @patch("rair.setup.Path.cwd")
    def test_setup_config_location_local_saves_to_local(self, mock_cwd, mock_is_git, mock_get_toplevel):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subdir = project_dir / "subdir"
            subdir.mkdir()

            mock_cwd.return_value = subdir
            mock_get_toplevel.return_value = project_dir
            mock_is_git.return_value = False

            result = setup_interactive(
                archive_dir="local_archive",
                input_patterns="local_data/*.json",
                output_patterns="",
                auto_discover=True,
                output_files_in_run=False,
                default_command="",
                config_location="local",
            )

            assert result.archive_dir == Path("local_archive")
            assert result.input_glob == ["local_data/*.json"]

            config_path = subdir / ".rair.toml"
            assert config_path.exists()
            content = config_path.read_text()
            assert 'archive_dir = "local_archive"' in content

    @patch("rair.setup.get_toplevel")
    @patch("rair.setup.is_git_project")
    @patch("rair.setup.Path.cwd")
    def test_setup_config_location_project_saves_to_project(self, mock_cwd, mock_is_git, mock_get_toplevel):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subdir = project_dir / "subdir"
            subdir.mkdir()

            mock_cwd.return_value = subdir
            mock_get_toplevel.return_value = project_dir
            mock_is_git.return_value = False

            result = setup_interactive(
                archive_dir="project_archive",
                input_patterns="data/*.csv",
                output_patterns="",
                auto_discover=True,
                output_files_in_run=False,
                default_command="",
                config_location="project",
            )

            config_path = project_dir / ".rair.toml"
            assert config_path.exists()
            content = config_path.read_text()
            assert 'archive_dir = "project_archive"' in content

    @patch("rair.setup.get_toplevel")
    @patch("rair.setup.is_git_project")
    @patch("rair.setup.Path.cwd")
    @patch("rair.setup.prompt")
    def test_setup_in_subdir_prompts_user(self, mock_prompt, mock_cwd, mock_is_git, mock_get_toplevel):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            subdir = project_dir / "subdir"
            subdir.mkdir()

            mock_cwd.return_value = subdir
            mock_get_toplevel.return_value = project_dir
            mock_is_git.return_value = False
            mock_prompt.return_value = "c"

            result = setup_interactive(
                archive_dir="test_archive",
                input_patterns="data/*.csv",
                output_patterns="",
                auto_discover=True,
                output_files_in_run=False,
                default_command="",
            )

            config_path = subdir / ".rair.toml"
            assert config_path.exists()

    @patch("rair.setup.get_toplevel")
    @patch("rair.setup.is_git_project")
    @patch("rair.setup.Path.cwd")
    def test_setup_no_auto_discover_with_patterns(self, mock_cwd, mock_is_git, mock_get_toplevel):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            mock_cwd.return_value = project_dir
            mock_get_toplevel.return_value = project_dir
            mock_is_git.return_value = False

            result = setup_interactive(
                archive_dir="archive",
                input_patterns="data/*.csv",
                output_patterns="results/*.json",
                auto_discover=False,
                output_files_in_run=False,
                default_command="",
                config_location="project",
            )

            assert result.auto_discover is False
            assert result.input_glob == ["data/*.csv"]
            assert result.output_glob == ["results/*.json"]


class TestGitignoreOperations:
    def test_read_gitignore_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir)
            result = read_gitignore(git_dir)
            assert result == []

    def test_read_gitignore_with_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir)
            gitignore = git_dir / ".gitignore"
            gitignore.write_text("*.pyc\n__pycache__/\n")

            result = read_gitignore(git_dir)
            assert "*.pyc" in result
            assert "__pycache__/" in result

    def test_add_gitignore_entries_new(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir)

            add_gitignore_entries(git_dir, ["new_entry1", "new_entry2"])

            result = read_gitignore(git_dir)
            assert "new_entry1" in result
            assert "new_entry2" in result

    def test_add_gitignore_entries_preserves_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = Path(tmpdir)
            gitignore = git_dir / ".gitignore"
            gitignore.write_text("existing_entry\n")

            add_gitignore_entries(git_dir, ["new_entry"])

            result = read_gitignore(git_dir)
            assert "existing_entry" in result
            assert "new_entry" in result


class TestIsGitProject:
    @patch("subprocess.run")
    def test_git_project_returns_true(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout.lower.return_value = "true"
        mock_run.return_value = mock_result

        result = is_git_project(Path("/some/path"))
        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_not_git_project_returns_false(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = is_git_project(Path("/some/path"))
        assert result is False