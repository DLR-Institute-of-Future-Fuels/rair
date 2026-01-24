"""Tests for cli_parser.py."""

from rair.cli_parser import (
    is_script_extension,
    parse_command_args,
    separate_args,
    SCRIPT_EXTENSIONS,
    RAIR_OPTIONS,
    RAIR_BOOLEAN_OPTIONS,
    ALL_RAIR_OPTIONS,
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
        assert is_script_extension("script.js") is False

    def test_with_path(self):
        assert is_script_extension("path/to/script.py") is True
        assert is_script_extension("path/to/script") is False
        assert is_script_extension("C:\\path\\to\\script.py") is True


class TestParseCommandArgs:
    def test_script_extension_auto_detect(self):
        command, script, remaining = parse_command_args(["myscript.py"])
        assert command is None
        assert script == "myscript.py"
        assert remaining == []

    def test_script_extension_with_args(self):
        command, script, remaining = parse_command_args(
            ["myscript.py", "arg1", "arg2"]
        )
        assert command is None
        assert script == "myscript.py"
        assert remaining == ["arg1", "arg2"]

    def test_explicit_command(self):
        command, script, remaining = parse_command_args(["python", "myscript.py"])
        assert command == "python"
        assert script == "myscript.py"
        assert remaining == []

    def test_explicit_command_with_args(self):
        command, script, remaining = parse_command_args(
            ["python", "myscript.py", "arg1", "arg2"]
        )
        assert command == "python"
        assert script == "myscript.py"
        assert remaining == ["arg1", "arg2"]

    def test_explicit_command_no_script(self):
        command, script, remaining = parse_command_args(["python"])
        assert command is None
        assert script == "python"
        assert remaining == []

    def test_empty_args(self):
        command, script, remaining = parse_command_args([])
        assert command is None
        assert script == ""
        assert remaining == []

    def test_bash_script(self):
        command, script, remaining = parse_command_args(["myscript.sh"])
        assert command is None
        assert script == "myscript.sh"
        assert remaining == []

    def test_make_command(self):
        command, script, remaining = parse_command_args(["make", "--all"])
        assert command == "make"
        assert script == "--all"
        assert remaining == []


class TestSeparateArgs:
    def test_no_args(self):
        rair_options, script_args = separate_args([])
        assert rair_options == []
        assert script_args == []

    def test_only_script_args(self):
        rair_options, script_args = separate_args(["arg1", "arg2"])
        assert rair_options == []
        assert script_args == ["arg1", "arg2"]

    def test_rair_option_with_value(self):
        rair_options, script_args = separate_args(
            ["--input", "data/*.csv", "arg1"]
        )
        assert rair_options == ["--input", "data/*.csv"]
        assert script_args == ["arg1"]

    def test_rair_option_without_value(self):
        rair_options, script_args = separate_args(
            ["--capture-output", "arg1"]
        )
        assert rair_options == ["--capture-output"]
        assert script_args == ["arg1"]

    def test_multiple_rair_options(self):
        rair_options, script_args = separate_args(
            [
                "--input",
                "data/*.csv",
                "--output",
                "results/*.txt",
                "arg1",
                "arg2",
            ]
        )
        assert rair_options == ["--input", "data/*.csv", "--output", "results/*.txt"]
        assert script_args == ["arg1", "arg2"]

    def test_separator(self):
        rair_options, script_args = separate_args(
            ["arg1", "--", "--input", "data.csv"]
        )
        assert rair_options == []
        assert script_args == ["arg1", "--input", "data.csv"]

    def test_separator_with_rair_options_before(self):
        rair_options, script_args = separate_args(
            ["--input", "data/*.csv", "--", "arg1", "--input"]
        )
        assert rair_options == ["--input", "data/*.csv"]
        assert script_args == ["arg1", "--input"]

    def test_unknown_option(self):
        rair_options, script_args = separate_args(["--unknown", "value"])
        assert rair_options == []
        assert script_args == ["--unknown", "value"]

    def test_mixed_case(self):
        rair_options, script_args = separate_args(
            ["arg1", "--Input", "data.csv", "arg2"]
        )
        assert rair_options == []
        assert script_args == ["arg1", "--Input", "data.csv", "arg2"]

    def test_option_like_script_arg(self):
        rair_options, script_args = separate_args(
            ["arg1", "--input", "data.csv"]
        )
        assert rair_options == ["--input", "data.csv"]
        assert script_args == ["arg1"]

    def test_rair_option_among_script_args(self):
        rair_options, script_args = separate_args(
            ["arg1", "--input", "data.csv", "arg2", "--output", "results.txt"]
        )
        assert rair_options == ["--input", "data.csv", "--output", "results.txt"]
        assert script_args == ["arg1", "arg2"]

    def test_separator_bypasses_option_detection(self):
        rair_options, script_args = separate_args(
            ["arg1", "--", "--input", "data.csv", "arg2", "--output", "results.txt"]
        )
        assert rair_options == []
        assert script_args == ["arg1", "--input", "data.csv", "arg2", "--output", "results.txt"]


class TestScriptExtensions:
    def test_script_extensions_set(self):
        expected = {".py", ".sh", ".bash", ".bat", ".cmd", ".exe"}
        assert SCRIPT_EXTENSIONS == expected


class TestRairOptions:
    def test_rair_options_set(self):
        expected = {
            "--config",
            "--input",
            "--output",
            "--exclude",
            "--archive-dir",
        }
        assert RAIR_OPTIONS == expected

    def test_rair_boolean_options_set(self):
        expected = {
            "--capture-output",
        }
        assert RAIR_BOOLEAN_OPTIONS == expected

    def test_all_rair_options_set(self):
        expected = {
            "--config",
            "--input",
            "--output",
            "--exclude",
            "--archive-dir",
            "--capture-output",
        }
        assert ALL_RAIR_OPTIONS == expected