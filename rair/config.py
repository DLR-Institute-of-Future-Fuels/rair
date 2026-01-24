"""Configuration loading for rair."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class RairConfig:
    """Configuration for a rair run."""

    archive_dir: Path = field(default_factory=lambda: Path("rairarchive"))
    input_glob: list[str] = field(default_factory=list[str])
    output_glob: list[str] = field(default_factory=list[str])
    exclude_glob: list[str] = field(default_factory=list[str])
    capture_output: bool = True


def find_config_file(project_dir: Path, config_name: Optional[str] = None) -> Optional[Path]:
    """Search for config file in project directory.

    Args:
        project_dir: Directory to search in
        config_name: Specific config file name (default: .rair.toml)

    Returns:
        Path to config file or None if not found
    """
    if config_name is None:
        config_name = ".rair.toml"

    config_path = project_dir / config_name
    if config_path.exists():
        return config_path

    return None


def find_pyproject_toml(project_dir: Path) -> Optional[Path]:
    """Search for pyproject.toml with [tool.rair] section."""
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        return pyproject_path
    return None


def load_toml_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from a TOML file.

    Args:
        config_path: Path to the TOML config file

    Returns:
        Dictionary with loaded configuration
    """
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def parse_rair_config(config_data: dict[str, Any]) -> RairConfig:
    """Parse rair configuration from loaded TOML data.

    Args:
        config_data: Dictionary from TOML file

    Returns:
        RairConfig instance
    """
    config = RairConfig()

    if "tool" in config_data and "rair" in config_data["tool"]:
        rair_config = config_data["tool"]["rair"]

        if "archive_dir" in rair_config:
            config.archive_dir = Path(rair_config["archive_dir"])

        if "input_glob" in rair_config:
            val = rair_config["input_glob"]
            config.input_glob = val if isinstance(val, list) else [val]

        if "output_glob" in rair_config:
            val = rair_config["output_glob"]
            config.output_glob = val if isinstance(val, list) else [val]

        if "exclude_glob" in rair_config:
            val = rair_config["exclude_glob"]
            config.exclude_glob = val if isinstance(val, list) else [val]

        if "capture_output" in rair_config:
            config.capture_output = bool(rair_config["capture_output"])

    elif "rair" in config_data:
        rair_config = config_data["rair"]

        if "archive_dir" in rair_config:
            config.archive_dir = Path(rair_config["archive_dir"])

        if "input_glob" in rair_config:
            val = rair_config["input_glob"]
            config.input_glob = val if isinstance(val, list) else [val]

        if "output_glob" in rair_config:
            val = rair_config["output_glob"]
            config.output_glob = val if isinstance(val, list) else [val]

        if "exclude_glob" in rair_config:
            val = rair_config["exclude_glob"]
            config.exclude_glob = val if isinstance(val, list) else [val]

        if "capture_output" in rair_config:
            config.capture_output = bool(rair_config["capture_output"])

    return config


def load_config(project_dir: Path, config_name: Optional[str] = None) -> RairConfig:
    """Load rair configuration from file.

    Searches for:
    1. .rair.toml in project directory
    2. pyproject.toml with [tool.rair] section

    Args:
        project_dir: Project directory to search
        config_name: Specific config file name (default: .rair.toml)

    Returns:
        RairConfig instance with loaded configuration
    """
    config_path = find_config_file(project_dir, config_name)

    if config_path is None:
        pyproject_path = find_pyproject_toml(project_dir)
        if pyproject_path is not None:
            config_data = load_toml_config(pyproject_path)
            return parse_rair_config(config_data)
        return RairConfig()

    config_data = load_toml_config(config_path)
    return parse_rair_config(config_data)


def merge_config_with_cli(
    config: RairConfig,
    cli_input: Optional[list[str]],
    cli_output: Optional[list[str]],
    cli_exclude: Optional[list[str]],
    cli_archive_dir: Optional[Path],
) -> RairConfig:
    """Merge file config with CLI arguments.

    CLI arguments override file configuration.

    Args:
        config: Loaded file configuration
        cli_input: CLI --input-glob value
        cli_output: CLI --output-glob value
        cli_exclude: CLI --exclude value
        cli_archive_dir: CLI --archive-dir value

    Returns:
        Merged RairConfig
    """
    if cli_input is not None:
        config.input_glob = cli_input

    if cli_output is not None:
        config.output_glob = cli_output

    if cli_exclude is not None:
        config.exclude_glob = cli_exclude

    if cli_archive_dir is not None:
        config.archive_dir = cli_archive_dir

    return config