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