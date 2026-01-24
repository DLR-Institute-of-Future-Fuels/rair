"""Tests for cli.py."""

import tempfile
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from rair.cli import app


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "data versioning" in result.output.lower()

    def test_run_script_not_found(self):
        runner = CliRunner()
        result = runner.invoke(app, ["nonexistent.py"])
        assert result.exit_code != 0

    def test_cli_with_minimal_args(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(app, [str(script_path)])
                assert result.exit_code == 0
                assert mock_run.called
            finally:
                script_path.unlink()

    def test_cli_with_bash_script(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".sh"
            ) as f:
                f.write("#!/bin/bash\necho 'hello'")
                script_path = Path(f.name)

            try:
                result = runner.invoke(app, [str(script_path)])
                assert result.exit_code == 0
                assert mock_run.called
            finally:
                script_path.unlink()

    def test_cli_with_script_args(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(app, [str(script_path), "arg1", "arg2"])
                assert result.exit_code == 0
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args[0][1] == ["arg1", "arg2"]
            finally:
                script_path.unlink()

    def test_cli_with_config_path(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / "test_config.toml"
                config_path.write_text("[rair]\n")

                try:
                    result = runner.invoke(app, [str(script_path), "--config", str(config_path)])
                    assert result.exit_code == 0
                    assert mock_run.called
                finally:
                    script_path.unlink()

    def test_cli_with_input_output_options(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(
                    app,
                    [
                        str(script_path),
                        "--input", "data/*.csv",
                        "--output", "results/*.txt",
                        "--exclude", "*.tmp",
                    ],
                )
                assert result.exit_code == 0
                assert mock_run.called
            finally:
                script_path.unlink()

    def test_cli_explicit_python_command(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(app, ["python", str(script_path)])
                assert result.exit_code == 0
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args[0][3] == "python"
            finally:
                script_path.unlink()

    def test_cli_explicit_python_command_with_script_args(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(app, ["python", str(script_path), "arg1", "arg2"])
                assert result.exit_code == 0
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args[0][1] == ["arg1", "arg2"]
                assert call_args[0][3] == "python"
            finally:
                script_path.unlink()

    def test_cli_explicit_bash_command(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".sh"
            ) as f:
                f.write("#!/bin/bash\necho 'hello'")
                script_path = Path(f.name)

            try:
                result = runner.invoke(app, ["bash", str(script_path)])
                assert result.exit_code == 0
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args[0][3] == "bash"
            finally:
                script_path.unlink()

    def test_cli_explicit_command_without_script_fails(self):
        runner = CliRunner()

        result = runner.invoke(app, ["python"])
        assert result.exit_code != 0
        assert "No script specified" in result.output

    def test_cli_auto_detect_with_rair_options(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(
                    app,
                    [
                        str(script_path),
                        "arg1",
                        "--input", "data/*.csv",
                    ],
                )
                assert result.exit_code == 0
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args[0][1] == ["arg1"]
            finally:
                script_path.unlink()

    def test_cli_explicit_command_with_rair_options(self):
        runner = CliRunner()

        with patch("rair.cli.run") as mock_run:
            mock_run.return_value = 0

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".py"
            ) as f:
                f.write("print('hello')")
                script_path = Path(f.name)

            try:
                result = runner.invoke(
                    app,
                    [
                        "python",
                        str(script_path),
                        "arg1",
                        "--input", "data/*.csv",
                    ],
                )
                assert result.exit_code == 0
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args[0][1] == ["arg1"]
                assert call_args[0][3] == "python"
            finally:
                script_path.unlink()