"""Tests for config.py."""

import tempfile
from pathlib import Path
import pytest

from rair.config import (
    RairConfig,
    find_config_file,
    find_pyproject_toml,
    load_toml_config,
    parse_rair_config,
    load_config,
    merge_config_with_cli,
)


class TestFindConfigFile:
    def test_find_existing_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".rair.toml"
            config_path.write_text("[rair]\n")

            result = find_config_file(Path(tmpdir))
            assert result == config_path

    def test_config_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_config_file(Path(tmpdir))
            assert result is None

    def test_custom_config_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_config = Path(tmpdir) / "my_rair.toml"
            custom_config.write_text("[rair]\n")

            result = find_config_file(Path(tmpdir), "my_rair.toml")
            assert result == custom_config


class TestFindPyprojectToml:
    def test_find_pyproject(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text("[project]\n")

            result = find_pyproject_toml(Path(tmpdir))
            assert result == pyproject_path

    def test_pyproject_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_pyproject_toml(Path(tmpdir))
            assert result is None


class TestLoadTomlConfig:
    def test_load_basic_config(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            f.write('archive_dir = "my_archive"\n')
            f.write('input_glob = ["data/*.csv"]\n')
            config_path = Path(f.name)

        try:
            result = load_toml_config(config_path)
            assert result["archive_dir"] == "my_archive"
            assert result["input_glob"] == ["data/*.csv"]
        finally:
            config_path.unlink()


class TestParseRairConfig:
    def test_parse_tool_rair_section(self):
        config_data = {
            "tool": {
                "rair": {
                    "archive_dir": "custom_archive",
                    "input_glob": ["data/*.csv"],
                    "output_glob": ["results/*.txt"],
                    "exclude_glob": ["*.tmp"],
                }
            }
        }

        result = parse_rair_config(config_data)

        assert result.archive_dir == Path("custom_archive")
        assert result.input_glob == ["data/*.csv"]
        assert result.output_glob == ["results/*.txt"]
        assert result.exclude_glob == ["*.tmp"]

    def test_parse_flat_rair_section(self):
        config_data = {
            "rair": {
                "archive_dir": "my_archive",
                "input_glob": "single_glob",
            }
        }

        result = parse_rair_config(config_data)

        assert result.archive_dir == Path("my_archive")
        assert result.input_glob == ["single_glob"]

    def test_parse_empty_config(self):
        result = parse_rair_config({})
        assert result.archive_dir == Path("rairarchive")
        assert result.input_glob == []
        assert result.output_glob == []
        assert result.exclude_glob == []


class TestLoadConfig:
    def test_load_from_rair_toml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".rair.toml"
            config_path.write_text("""
[rair]
archive_dir = "test_archive"
input_glob = ["data/*.csv"]
""")

            result = load_config(Path(tmpdir))

            assert result.archive_dir == Path("test_archive")
            assert result.input_glob == ["data/*.csv"]

    def test_load_from_pyproject_toml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text("""
[tool.rair]
archive_dir = "pyproject_archive"
input_glob = ["input/*.json"]
""")

            result = load_config(Path(tmpdir))

            assert result.archive_dir == Path("pyproject_archive")
            assert result.input_glob == ["input/*.json"]

    def test_prefer_rair_toml_over_pyproject(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rair_config = Path(tmpdir) / ".rair.toml"
            rair_config.write_text('[rair]\narchive_dir = "rair_toml_dir"\n')

            pyproject_path = Path(tmpdir) / "pyproject.toml"
            pyproject_path.write_text('[tool.rair]\narchive_dir = "pyproject_dir"\n')

            result = load_config(Path(tmpdir))

            assert result.archive_dir == Path("rair_toml_dir")

    def test_default_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_config(Path(tmpdir))

            assert result.archive_dir == Path("rairarchive")
            assert result.input_glob == []


class TestMergeConfigWithCli:
    def test_cli_overrides_all(self):
        config = RairConfig(
            archive_dir=Path("config_archive"),
            input_glob=["config_input/*.csv"],
            output_glob=["config_output/*.txt"],
            exclude_glob=["config_exclude/*.log"],
        )

        result = merge_config_with_cli(
            config,
            cli_input=["cli_input/*.csv"],
            cli_output=["cli_output/*.txt"],
            cli_exclude=["cli_exclude/*.tmp"],
            cli_archive_dir=Path("cli_archive"),
        )

        assert result.archive_dir == Path("cli_archive")
        assert result.input_glob == ["cli_input/*.csv"]
        assert result.output_glob == ["cli_output/*.txt"]
        assert result.exclude_glob == ["cli_exclude/*.tmp"]

    def test_cli_partially_overrides(self):
        config = RairConfig(
            archive_dir=Path("config_archive"),
            input_glob=["config_input/*.csv"],
            output_glob=["config_output/*.txt"],
        )

        result = merge_config_with_cli(
            config,
            cli_input=["cli_input/*.csv"],
            cli_output=None,
            cli_exclude=None,
            cli_archive_dir=None,
        )

        assert result.archive_dir == Path("config_archive")
        assert result.input_glob == ["cli_input/*.csv"]
        assert result.output_glob == ["config_output/*.txt"]

    def test_none_cli_keeps_config(self):
        config = RairConfig(
            archive_dir=Path("config_archive"),
            input_glob=["config_input/*.csv"],
        )

        result = merge_config_with_cli(
            config,
            cli_input=None,
            cli_output=None,
            cli_exclude=None,
            cli_archive_dir=None,
        )

        assert result.archive_dir == Path("config_archive")
        assert result.input_glob == ["config_input/*.csv"]