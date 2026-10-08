"""Tests for script_type.py."""

import os
import sys
from pathlib import Path
from typing import Optional

import pytest

from rair.cli_parser import is_script
from rair.script_type import (
    find_python,
    get_script_command,
    parse_shebang,
)


def available(monkeypatch: pytest.MonkeyPatch, *names: str) -> None:
    """Pretend that exactly the given executables are found on the PATH."""
    def which(name: str) -> Optional[str]:
        return f"/usr/bin/{name}" if name in names else None

    monkeypatch.setattr("rair.script_type.shutil.which", which)


def write_script(tmp_path: Path, name: str, content: str) -> Path:
    script_path = tmp_path / name
    script_path.write_bytes(content.encode())
    return script_path


class TestFindPython:
    def test_python_on_path_is_preferred(self, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python", "python3")
        assert find_python() == "python"

    def test_python3_if_python_is_missing(self, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python3")
        assert find_python() == "python3"

    def test_falls_back_to_interpreter_of_rair(self, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch)
        assert find_python() == sys.executable

    def test_windows_store_stub_is_ignored(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr("rair.script_type.os.name", "nt")
        monkeypatch.setattr(
            "rair.script_type.shutil.which",
            lambda name: f"C:\\Users\\me\\AppData\\Local\\Microsoft\\WindowsApps\\{name}.EXE",
        )
        assert find_python() == sys.executable


class TestParseShebang:
    def test_no_shebang(self, tmp_path: Path):
        assert parse_shebang(write_script(tmp_path, "script", "print('hello')\n")) is None

    def test_missing_file(self, tmp_path: Path):
        assert parse_shebang(tmp_path / "missing") is None

    def test_empty_shebang(self, tmp_path: Path):
        assert parse_shebang(write_script(tmp_path, "script", "#!\necho\n")) is None

    def test_absolute_interpreter(self, tmp_path: Path):
        assert parse_shebang(write_script(tmp_path, "script", "#!/bin/bash\necho\n")) == ["/bin/bash"]

    def test_interpreter_with_arguments(self, tmp_path: Path):
        script_path = write_script(tmp_path, "script", "#! /usr/bin/perl -w\n")
        assert parse_shebang(script_path) == ["/usr/bin/perl", "-w"]

    def test_env_is_removed(self, tmp_path: Path):
        script_path = write_script(tmp_path, "script", "#!/usr/bin/env python3\n")
        assert parse_shebang(script_path) == ["python3"]

    def test_env_options_are_removed(self, tmp_path: Path):
        script_path = write_script(tmp_path, "script", "#!/usr/bin/env -S VAR=1 uv run --script\n")
        assert parse_shebang(script_path) == ["uv", "run", "--script"]

    def test_windows_line_ending(self, tmp_path: Path):
        script_path = write_script(tmp_path, "script", "#!/usr/bin/env node\r\nconsole.log(1)\r\n")
        assert parse_shebang(script_path) == ["node"]

    def test_binary_file(self, tmp_path: Path):
        script_path = tmp_path / "binary"
        script_path.write_bytes(b"\x7fELF\x00\x01\x02")
        assert parse_shebang(script_path) is None


class TestGetScriptCommand:
    def test_python_extension(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python")
        script_path = write_script(tmp_path, "script.py", "print('hello')\n")
        assert get_script_command(script_path) == ["python", str(script_path)]

    def test_python_shebang_without_extension(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python", "python3")
        script_path = write_script(tmp_path, "script", "#!/usr/bin/env python3\nprint('hello')\n")
        assert get_script_command(script_path) == ["python", str(script_path)]

    def test_system_python_shebang_uses_python_on_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python3")
        script_path = write_script(tmp_path, "script", "#!/usr/bin/python\nprint('hello')\n")
        assert get_script_command(script_path) == ["python3", str(script_path)]

    def test_versioned_python_shebang(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        script_path = write_script(tmp_path, "script.py", "#!/usr/bin/env python3.11\n")
        available(monkeypatch, "python", "python3.11")
        assert get_script_command(script_path) == ["python3.11", str(script_path)]
        available(monkeypatch, "python")
        assert get_script_command(script_path) == ["python", str(script_path)]

    def test_shebang_with_specific_interpreter(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python")
        interpreter = write_script(tmp_path, "mypython", "")
        script_path = write_script(tmp_path, "script.py", f"#!{interpreter.as_posix()} -u\n")
        assert get_script_command(script_path) == [interpreter.as_posix(), "-u", str(script_path)]

    def test_shebang_with_other_interpreter(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "Rscript")
        script_path = write_script(tmp_path, "analysis", "#!/usr/bin/env Rscript\n")
        assert get_script_command(script_path) == ["Rscript", str(script_path)]

    def test_shebang_arguments_are_kept(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "uv")
        script_path = write_script(tmp_path, "script.py", "#!/usr/bin/env -S uv run --script\n")
        assert get_script_command(script_path) == ["uv", "run", "--script", str(script_path)]

    def test_shebang_takes_precedence_over_extension(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        available(monkeypatch, "python", "bash")
        script_path = write_script(tmp_path, "script.py", "#!/usr/bin/env bash\necho 'hello'\n")
        assert get_script_command(script_path) == ["bash", str(script_path)]

    def test_extension_is_used_if_shebang_interpreter_is_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        available(monkeypatch, "bash")
        script_path = write_script(tmp_path, "script.sh", "#!/usr/bin/env zsh\necho 'hello'\n")
        assert get_script_command(script_path) == ["bash", str(script_path)]

    @pytest.mark.parametrize("name, command", [
        ("script.sh", ["bash"]),
        ("script.bash", ["bash"]),
        ("script.ps1", ["pwsh", "-File"]),
        ("script.R", ["Rscript"]),
        ("script.jl", ["julia"]),
        ("script.js", ["node"]),
        ("script.pl", ["perl"]),
        ("script.rb", ["ruby"]),
    ])
    def test_extensions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, command: list[str]
    ):
        available(monkeypatch, command[0])
        script_path = write_script(tmp_path, name, "content\n")
        assert get_script_command(script_path) == command + [str(script_path)]

    def test_fallback_interpreter_of_extension(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        script_path = write_script(tmp_path, "script.ps1", "content\n")
        available(monkeypatch, "powershell")
        assert get_script_command(script_path) == ["powershell", "-File", str(script_path)]
        # The preferred interpreter is reported as missing when running the command
        available(monkeypatch)
        assert get_script_command(script_path) == ["pwsh", "-File", str(script_path)]

    @pytest.mark.parametrize("name", ["tool.exe", "script.bat", "script.cmd"])
    def test_executables_are_run_directly(self, tmp_path: Path, name: str):
        script_path = write_script(tmp_path, name, "#!/bin/bash\n")
        assert get_script_command(script_path) == [str(script_path)]

    def test_unknown_file_is_run_directly(self, tmp_path: Path):
        script_path = write_script(tmp_path, "script.unknown", "content\n")
        assert get_script_command(script_path) == [str(script_path)]

    def test_file_without_directory_is_not_searched_on_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        write_script(tmp_path, "tool", "content\n")
        monkeypatch.chdir(tmp_path)
        expected = "tool" if os.name == "nt" else "./tool"
        assert get_script_command(Path("tool")) == [expected]


class TestIsScript:
    def test_known_extension(self):
        assert is_script("missing.py") is True
        assert is_script("analysis.R") is True
        assert is_script("model.jl") is True

    def test_file_with_shebang(self, tmp_path: Path):
        script_path = write_script(tmp_path, "run_model", "#!/usr/bin/env python\n")
        assert is_script(str(script_path)) is True

    def test_file_without_shebang_is_a_command(self, tmp_path: Path):
        script_path = write_script(tmp_path, "Makefile", "all:\n")
        assert is_script(str(script_path)) is False

    def test_command(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(tmp_path)
        assert is_script("make") is False

    def test_directory_is_a_command(self, tmp_path: Path):
        assert is_script(str(tmp_path)) is False
