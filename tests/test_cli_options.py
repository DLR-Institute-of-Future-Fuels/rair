"""Tests for the mapping of CLI options to the run configuration."""

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from rair.cli import app
from rair.config import RairConfig


@pytest.fixture
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty directory used as working and project directory."""
    (tmp_path / "script.py").write_text("print('hello')")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def invoke(cli_args: list[str]) -> tuple[Any, Any]:
    """Invoke the CLI with a mocked run function and return (result, call_args of run)."""
    runner = CliRunner()
    with patch("rair.cli.run") as mock_run, patch("rair.cli.get_toplevel") as mock_toplevel:
        mock_run.return_value = 0
        mock_toplevel.return_value = Path.cwd()
        result = runner.invoke(app, cli_args)
        return result, mock_run.call_args


def invoke_config(cli_args: list[str]) -> RairConfig:
    """Invoke the CLI and return the RairConfig that is passed to run."""
    result, call_args = invoke(cli_args)
    assert result.exit_code == 0, result.output
    config = call_args[0][3]
    assert isinstance(config, RairConfig)
    return config


class TestBooleanFlags:
    def test_defaults(self, project_dir: Path):
        config = invoke_config(["script.py"])
        assert config.capture_output is True
        assert config.auto_discover is True
        assert config.output_files_in_run is True

    def test_no_capture_output(self, project_dir: Path):
        config = invoke_config(["--no-capture-output", "script.py"])
        assert config.capture_output is False
        assert config.auto_discover is True
        assert config.output_files_in_run is True

    def test_no_auto_discover(self, project_dir: Path):
        config = invoke_config(["--no-auto-discover", "script.py"])
        assert config.capture_output is True
        assert config.auto_discover is False
        assert config.output_files_in_run is True

    def test_no_output_files_in_run(self, project_dir: Path):
        config = invoke_config(["--no-output-files-in-run", "script.py"])
        assert config.capture_output is True
        assert config.auto_discover is True
        assert config.output_files_in_run is False

    def test_cli_flags_override_config_file(self, project_dir: Path):
        (project_dir / ".rair.toml").write_text(
            "[rair]\ncapture_output = false\nauto_discover = false\noutput_files_in_run = false\n"
        )
        config = invoke_config(["script.py"])
        assert config.capture_output is False
        assert config.auto_discover is False
        assert config.output_files_in_run is False

        config = invoke_config(
            ["--capture-output", "--auto-discover", "--output-files-in-run", "script.py"]
        )
        assert config.capture_output is True
        assert config.auto_discover is True
        assert config.output_files_in_run is True


class TestValueOptions:
    def test_comment_is_passed_to_run(self, project_dir: Path):
        config = invoke_config(["--comment", "experiment 1", "script.py"])
        assert config.comment == "experiment 1"

    def test_glob_options(self, project_dir: Path):
        config = invoke_config([
            "--input", "data/*.csv", "--input", "parameters.txt",
            "--output", "results/*.json",
            "--exclude", "*.tmp",
            "script.py",
        ])
        assert config.input_glob == ["data/*.csv", "parameters.txt"]
        assert config.output_glob == ["results/*.json"]
        assert config.exclude_glob == ["*.tmp"]

    def test_autodata_defaults_to_project_dir(self, project_dir: Path):
        config = invoke_config(["script.py"])
        assert config.autodata_dir == project_dir

    def test_autodata_from_cli(self, project_dir: Path):
        config = invoke_config(["--autodata", "data", "script.py"])
        assert config.autodata_dir == (project_dir / "data").resolve()

    def test_autodata_from_config_file_is_kept(self, project_dir: Path):
        (project_dir / ".rair.toml").write_text('[rair]\nautodata_dir = "data"\n')
        config = invoke_config(["script.py"])
        assert config.autodata_dir == Path("data")

    def test_config_file_in_other_directory(self, project_dir: Path):
        config_dir = project_dir / "configs"
        config_dir.mkdir()
        (config_dir / "special.toml").write_text('[rair]\narchive_dir = "special_archive"\n')
        # Must take precedence over the config in the working directory
        (project_dir / ".rair.toml").write_text('[rair]\narchive_dir = "default_archive"\n')

        config = invoke_config(["--config", "configs/special.toml", "script.py"])
        assert config.archive_dir == Path("special_archive")

    def test_missing_config_file_is_an_error(self, project_dir: Path):
        result, call_args = invoke(["--config", "missing.toml", "script.py"])
        assert result.exit_code == 1
        assert "Config file not found" in result.output
        assert call_args is None


class TestScriptArguments:
    def test_unknown_options_are_passed_to_script(self, project_dir: Path):
        result, call_args = invoke(["script.py", "--lr", "0.1", "-v"])
        assert result.exit_code == 0, result.output
        assert call_args[0][0] == Path("script.py")
        assert call_args[0][2] == ["--lr", "0.1", "-v"]

    def test_unknown_options_are_passed_to_command(self, project_dir: Path):
        result, call_args = invoke(["make", "--all"])
        assert result.exit_code == 0, result.output
        assert call_args[0][0] == Path("--all")
        assert call_args[0][2] == []
        assert call_args[0][4] == "make"

    def test_double_dash_passes_rair_options_to_script(self, project_dir: Path):
        result, call_args = invoke(["script.py", "--", "--input", "file.txt"])
        assert result.exit_code == 0, result.output
        assert call_args[0][2] == ["--input", "file.txt"]
        assert call_args[0][3].input_glob == []


class TestDefaultCommand:
    def test_no_command_and_no_default_is_an_error(self, project_dir: Path):
        result, call_args = invoke([])
        assert result.exit_code == 1
        assert call_args is None

    def test_default_command(self, project_dir: Path):
        (project_dir / ".rair.toml").write_text('[rair]\ndefault_command = "make"\n')
        result, call_args = invoke(["--comment", "experiment 1"])
        assert result.exit_code == 0, result.output
        assert call_args[0][0] is None
        assert call_args[0][4] == "make"
        assert call_args[0][3].comment == "experiment 1"

    def test_default_command_with_arguments(self, project_dir: Path):
        (project_dir / ".rair.toml").write_text('[rair]\ndefault_command = "python script.py a b"\n')
        result, call_args = invoke([])
        assert result.exit_code == 0, result.output
        assert call_args[0][0] == Path("script.py")
        assert call_args[0][2] == ["a", "b"]
        assert call_args[0][4] == "python"

    def test_default_script(self, project_dir: Path):
        (project_dir / ".rair.toml").write_text('[rair]\ndefault_command = "script.py --fast"\n')
        result, call_args = invoke([])
        assert result.exit_code == 0, result.output
        assert call_args[0][0] == Path("script.py")
        assert call_args[0][2] == ["--fast"]
        assert call_args[0][4] is None


class TestExecutionDir:
    def test_execution_dir_is_cwd(self, project_dir: Path):
        result, call_args = invoke(["script.py"])
        assert result.exit_code == 0, result.output
        assert call_args[0][5] == Path(os.getcwd())
