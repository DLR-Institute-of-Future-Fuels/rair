"""Tests for cli_parser.py."""

from rair.cli_parser import (
    is_script_extension,
    SCRIPT_EXTENSIONS,
)


class TestIsScriptExtension:
    def test_python_extension(self):
        assert is_script_extension("script.py") is True
        assert is_script_extension("SCRIPT.PY") is True

    def test_bash_extension(self):
        assert is_script_extension("script.sh") is True
        assert is_script_extension("SCRIPT.SH") is True

    def test_bash_long_extension(self):
        assert is_script_extension("script.bash") is True
        assert is_script_extension("SCRIPT.BASH") is True

    def test_exe_extension(self):
        assert is_script_extension("program.exe") is True
        assert is_script_extension("PROGRAM.EXE") is True

    def test_bat_extension(self):
        assert is_script_extension("script.bat") is True
        assert is_script_extension("SCRIPT.BAT") is True

    def test_cmd_extension(self):
        assert is_script_extension("script.cmd") is True
        assert is_script_extension("SCRIPT.CMD") is True

    def test_no_extension(self):
        assert is_script_extension("script") is False
        assert is_script_extension("make") is False
        assert is_script_extension("python") is False

    def test_unknown_extension(self):
        assert is_script_extension("script.txt") is False
        assert is_script_extension("script.log") is False
        assert is_script_extension("script.xyz") is False

    def test_with_path(self):
        assert is_script_extension("path/to/script.py") is True
        assert is_script_extension("path/to/script") is False
        assert is_script_extension("C:\\path\\to\\script.py") is True


class TestScriptExtensions:
    def test_script_extensions_set(self):
        expected = {".py", ".sh", ".bash", ".bat", ".cmd", ".exe", ".ps1"}
        assert expected <= SCRIPT_EXTENSIONS
