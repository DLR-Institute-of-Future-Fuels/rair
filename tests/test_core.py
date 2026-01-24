"""Tests for core.py - script execution with different types."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from rair.core import run
from rair.config import RairConfig


class TestRunScriptExecution:
    def test_run_python_script(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("print('hello from python')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            exit_code = run(script_path, [], config)
            assert exit_code == 0

    def test_run_python_script_with_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("""
import sys
print('arg1:', sys.argv[1] if len(sys.argv) > 1 else 'none')
print('arg2:', sys.argv[2] if len(sys.argv) > 2 else 'none')
""")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            exit_code = run(script_path, ["test_arg1", "test_arg2"], config)
            assert exit_code == 0

    def test_run_python_script_with_capture_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("print('hello from python')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=True,
            )

            exit_code = run(script_path, [], config)
            assert exit_code == 0

    def test_run_bash_script(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.sh"
            script_path.write_text("#!/bin/bash\necho 'hello from bash'")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config)

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert "bash" in called_command
                    assert str(script_path) in called_command
                    assert exit_code == 0

    def test_run_bash_script_shebang_without_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test_script"
            script_path.write_text("#!/bin/bash\necho 'hello from bash'")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config)

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert "bash" in called_command
                    assert str(script_path) in called_command
                    assert exit_code == 0

    def test_run_python_script_shebang_without_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test_script"
            script_path.write_text("#!/usr/bin/env python\nprint('hello')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config)

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert "python" in called_command
                    assert str(script_path) in called_command
                    assert exit_code == 0

    def test_run_other_executable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.exe"
            script_path.write_text("executable content")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config)

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert called_command == [str(script_path)]
                    assert exit_code == 0

    def test_run_with_input_output_tracking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("""
import sys
with open('output.txt', 'w') as f:
    f.write('output content')
""")

            input_file = tmpdir_path / "input.txt"
            input_file.write_text("input content")

            config = RairConfig(
                input_glob=["input.txt"],
                output_glob=["output.txt"],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            exit_code = run(script_path, [], config)
            assert exit_code == 0

    def test_run_script_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("import sys\nsys.exit(1)")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            exit_code = run(script_path, [], config)
            assert exit_code == 1

    def test_run_preserves_working_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()

            script_path = tmpdir_path / "test.py"
            script_path.write_text("print('hello')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            run(script_path, [], config)
            assert os.getcwd() == original_cwd


class TestRunWithCommandOverride:
    def test_run_with_command_override_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("print('hello')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config, command_override="python")

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert called_command[0] == "python"
                    assert str(script_path) in called_command
                    assert exit_code == 0

    def test_run_with_command_override_bash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.sh"
            script_path.write_text("#!/bin/bash\necho 'hello'")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config, command_override="bash")

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert called_command[0] == "bash"
                    assert str(script_path) in called_command
                    assert exit_code == 0

    def test_run_with_command_override_make(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "Makefile"
            script_path.write_text("all:\n\techo 'hello'")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, ["--all"], config, command_override="make")

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert called_command[0] == "make"
                    assert "--all" in called_command
                    assert exit_code == 0

    def test_run_command_override_with_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("print('hello')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, ["--arg1", "--arg2"], config, command_override="python")

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert called_command == ["python", str(script_path), "--arg1", "--arg2"]
                    assert exit_code == 0

    def test_run_without_command_override_uses_auto_detect(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "test.py"
            script_path.write_text("print('hello')")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "test"
                with patch("rair.core.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)

                    exit_code = run(script_path, [], config)

                    assert mock_run.called
                    called_command = mock_run.call_args[0][0]
                    assert "python" in called_command[0].lower()
                    assert str(script_path) in called_command
                    assert exit_code == 0


class TestAutoDiscoveryFeature:
    def test_input_fallback_all_tracked_as_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "script.py"
            script_path.write_text("print('hello')")

            input_file = tmpdir_path / "input.txt"
            input_file.write_text("input data")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                autodata_dir=tmpdir_path,
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = ""
                exit_code = run(script_path, [], config)

            assert exit_code == 0

    def test_excludes_git_tracked_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "script.py"
            script_path.write_text("print('hello')")

            tracked_file = tmpdir_path / "tracked.py"
            tracked_file.write_text("tracked code")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                autodata_dir=tmpdir_path,
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = "tracked.py"
                exit_code = run(script_path, [], config)

            assert exit_code == 0

    def test_excludes_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "script.py"
            script_path.write_text("print('hello')")

            hidden_file = tmpdir_path / ".secret"
            hidden_file.write_text("secret")

            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                autodata_dir=tmpdir_path,
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = ""
                exit_code = run(script_path, [], config)

            assert exit_code == 0

    def test_excludes_hidden_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "script.py"
            script_path.write_text("print('hello')")

            cache_dir = tmpdir_path / ".cache"
            cache_dir.mkdir()
            config = RairConfig(
                input_glob=[],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                autodata_dir=tmpdir_path,
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = ""
                exit_code = run(script_path, [], config)

            assert exit_code == 0

    def test_fallback_disabled_by_input_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            script_path = tmpdir_path / "script.py"
            script_path.write_text("print('hello')")

            config = RairConfig(
                input_glob=["*.py"],
                output_glob=[],
                exclude_glob=[],
                archive_dir=tmpdir_path / "archive",
                autodata_dir=tmpdir_path,
                capture_output=False,
            )

            with patch("rair.git._call_git_command") as mock_git:
                mock_git.return_value = ""
                exit_code = run(script_path, [], config)

            assert exit_code == 0