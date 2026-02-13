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
    autodata_dir: Optional[Path] = None
    capture_output: bool = True
    auto_discover: bool = True
    output_files_in_run: bool = False
    default_command: Optional[str] = None


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


def normalize_path(path: Path | str) -> str:
    """Normalize path to use forward slashes for cross-platform compatibility."""
    return str(path).replace("\\", "/")


def _normalize_glob_value(val: Any) -> list[str]:
    """Normalize glob fields that accept string or list.

    Converts backslashes to forward slashes for cross-platform compatibility.
    """
    values = [v for v in val if isinstance(v, str)] if isinstance(val, list) else [str(val)]
    return [v.replace("\\", "/") for v in values]


def _parse_rair_section(rair_config: dict[str, Any], config: RairConfig, field_map: dict[str, str]) -> None:
    """Parse rair config section and update config object.

    Args:
        rair_config: Raw config dictionary from TOML
        config: RairConfig instance to update
        field_map: Mapping of TOML field names to config field names
    """
    import sys
    
    known_fields = set(field_map.keys())
    unknown_fields = set(rair_config.keys()) - known_fields
    
    for unknown in unknown_fields:
        print(f"[WARNING] Unknown config setting '{unknown}' in config file", file=sys.stderr)
    
    for toml_field, config_field in field_map.items():
        if toml_field in rair_config:
            val = rair_config[toml_field]
            if config_field in ["input_glob", "output_glob", "exclude_glob"]:
                val = _normalize_glob_value(val)
            elif config_field in ["archive_dir", "autodata_dir"]:
                val = Path(val)
            elif config_field in ["capture_output", "auto_discover", "output_files_in_run"]:
                val = bool(val)
            setattr(config, config_field, val)


def parse_rair_config(config_data: dict[str, Any]) -> RairConfig:
    """Parse rair configuration from loaded TOML data.

    Args:
        config_data: Dictionary from TOML file

    Returns:
        RairConfig instance
    """
    config = RairConfig()
    
    field_map = {
        "archive_dir": "archive_dir",
        "input_glob": "input_glob",
        "input": "input_glob",
        "output_glob": "output_glob",
        "output": "output_glob",
        "exclude_glob": "exclude_glob",
        "exclude": "exclude_glob",
        "capture_output": "capture_output",
        "autodata_dir": "autodata_dir",
        "auto_discover": "auto_discover",
        "output_files_in_run": "output_files_in_run",
        "default_command": "default_command",
    }

    if "tool" in config_data and "rair" in config_data["tool"]:
        _parse_rair_section(config_data["tool"]["rair"], config, field_map)
    elif "rair" in config_data:
        _parse_rair_section(config_data["rair"], config, field_map)

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


def load_hierarchical_config(
    execution_dir: Path,
    project_dir: Path,
    config_name: Optional[str] = None,
) -> RairConfig:
    """Load rair configuration with hierarchical lookup.

    First checks execution_dir for a local config file. If found, uses it
    and ignores project-level config. If not found, falls back to project_dir.

    This allows different directories to have different configurations without
    merging - local config completely overrides project config.

    Args:
        execution_dir: Current working directory (checked first)
        project_dir: Project root directory (fallback)
        config_name: Specific config file name (default: .rair.toml)

    Returns:
        RairConfig instance with loaded configuration
    """
    local_config_path = find_config_file(execution_dir, config_name)
    if local_config_path is not None:
        config_data = load_toml_config(local_config_path)
        return parse_rair_config(config_data)

    local_pyproject_path = find_pyproject_toml(execution_dir)
    if local_pyproject_path is not None:
        config_data = load_toml_config(local_pyproject_path)
        return parse_rair_config(config_data)

    return load_config(project_dir, config_name)


def merge_config_with_cli(
    config: RairConfig,
    cli_input: Optional[list[str]],
    cli_output: Optional[list[str]],
    cli_exclude: Optional[list[str]],
    cli_archive_dir: Optional[Path],
    cli_autodata: Optional[Path] = None,
    cli_auto_discover: Optional[bool] = None,
    cli_output_files_in_run: Optional[bool] = None,
) -> RairConfig:
    """Merge file config with CLI arguments.

    CLI arguments override file configuration.

    Args:
        config: Loaded file configuration
        cli_input: CLI --input-glob value
        cli_output: CLI --output-glob value
        cli_exclude: CLI --exclude value
        cli_archive_dir: CLI --archive-dir value
        cli_autodata: CLI --autodata value
        cli_auto_discover: CLI --no-auto-discover value
        cli_output_files_in_run: CLI --output-files-in-run value

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

    if cli_autodata is not None:
        config.autodata_dir = cli_autodata

    if cli_auto_discover is not None:
        config.auto_discover = cli_auto_discover

    if cli_output_files_in_run is not None:
        config.output_files_in_run = cli_output_files_in_run

    return config