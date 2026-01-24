"""Tests for script_type.py."""

import tempfile
from pathlib import Path

from rair.script_type import (
    detect_script_type,
    get_command_args,
    get_run_command,
    make_executable,
)


class TestDetectScriptType:
    def test_python_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('hello')")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_bash_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("echo 'hello'")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "bash"
        finally:
            script_path.unlink()

    def test_exe_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".exe") as f:
            f.write("executable content")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_bat_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bat") as f:
            f.write("@echo off")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_cmd_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cmd") as f:
            f.write("@echo off")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_python_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/usr/bin/env python\nprint('hello')")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_python3_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/usr/bin/python3\nprint('hello')")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_bash_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/bin/bash\necho 'hello'")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "bash"
        finally:
            script_path.unlink()

    def test_shebang_extension_takes_precedence(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("#!/bin/bash\necho 'hello'")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "python"
        finally:
            script_path.unlink()

    def test_no_extension_no_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("some random content")
            f.flush()
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()

    def test_unrecognized_extension(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".unknown") as f:
            f.write("content")
            script_path = Path(f.name)
        try:
            result = detect_script_type(script_path)
            assert result == "other"
        finally:
            script_path.unlink()


class TestGetCommandArgs:
    def test_python_command(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('hello')")
            script_path = Path(f.name)
        try:
            result = get_command_args(script_path, "python")
            assert result == ["python", str(script_path)]
        finally:
            script_path.unlink()

    def test_bash_command(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("echo 'hello'")
            script_path = Path(f.name)
        try:
            result = get_command_args(script_path, "bash")
            assert result == ["bash", str(script_path)]
        finally:
            script_path.unlink()

    def test_other_command(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("executable content")
            script_path = Path(f.name)
        try:
            result = get_command_args(script_path, "other")
            assert result == [str(script_path)]
        finally:
            script_path.unlink()


class TestGetRunCommand:
    def test_python_script(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("print('hello')")
            script_path = Path(f.name)
        try:
            command, script_type = get_run_command(script_path)
            assert script_type == "python"
            assert command == ["python", str(script_path)]
        finally:
            script_path.unlink()

    def test_bash_script(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("echo 'hello'")
            script_path = Path(f.name)
        try:
            command, script_type = get_run_command(script_path)
            assert script_type == "bash"
            assert command == ["bash", str(script_path)]
        finally:
            script_path.unlink()

    def test_exe_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".exe") as f:
            f.write("executable content")
            script_path = Path(f.name)
        try:
            command, script_type = get_run_command(script_path)
            assert script_type == "other"
            assert command == [str(script_path)]
        finally:
            script_path.unlink()

    def test_python_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/usr/bin/env python\nprint('hello')")
            f.flush()
            script_path = Path(f.name)
        try:
            command, script_type = get_run_command(script_path)
            assert script_type == "python"
            assert command == ["python", str(script_path)]
        finally:
            script_path.unlink()

    def test_bash_shebang(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("#!/bin/bash\necho 'hello'")
            f.flush()
            script_path = Path(f.name)
        try:
            command, script_type = get_run_command(script_path)
            assert script_type == "bash"
            assert command == ["bash", str(script_path)]
        finally:
            script_path.unlink()


class TestMakeExecutable:
    def test_make_executable_success(self):
        import sys
        import stat

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("#!/bin/bash\necho 'hello'")
            script_path = Path(f.name)
        try:
            result = make_executable(script_path)
            assert result is True

            if sys.platform != "win32":
                current_mode = script_path.stat().st_mode
                assert current_mode & stat.S_IXUSR != 0
        finally:
            script_path.unlink()

    def test_make_executable_nonexistent_file(self):
        result = make_executable(Path("/nonexistent/path/script.sh"))
        assert result is False

    def test_make_executable_already_executable(self):
        import sys
        import stat

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("#!/bin/bash\necho 'hello'")
            script_path = Path(f.name)
        try:
            if sys.platform != "win32":
                script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)
            result = make_executable(script_path)
            assert result is True
        finally:
            script_path.unlink()