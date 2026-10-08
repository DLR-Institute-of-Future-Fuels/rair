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
    output_files_in_run: bool = True
    default_command: Optional[str] = None
    comment: Optional[str] = None


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


# Mapping of TOML setting names to RairConfig field names
FIELD_MAP = {
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


def _get_rair_section(config_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Get the rair section ([tool.rair] or [rair]) from loaded TOML data."""
    if "tool" in config_data and "rair" in config_data["tool"]:
        section: dict[str, Any] = config_data["tool"]["rair"]
        return section
    if "rair" in config_data:
        section = config_data["rair"]
        return section
    return None


def _parse_rair_section(rair_config: dict[str, Any]) -> dict[str, Any]:
    """Parse a rair config section into values for the RairConfig fields.

    Only settings that are present in the section are returned, so that
    several sections can be merged without overwriting values by defaults.

    Args:
        rair_config: Raw config dictionary from TOML

    Returns:
        Mapping of RairConfig field names to parsed values
    """
    unknown_fields = set(rair_config.keys()) - set(FIELD_MAP.keys())

    for unknown in unknown_fields:
        print(f"[WARNING] Unknown config setting '{unknown}' in config file", file=sys.stderr)

    settings: dict[str, Any] = {}
    for toml_field, config_field in FIELD_MAP.items():
        if toml_field in rair_config:
            val = rair_config[toml_field]
            if config_field in ["input_glob", "output_glob", "exclude_glob"]:
                val = _normalize_glob_value(val)
            elif config_field in ["archive_dir", "autodata_dir"]:
                val = Path(val)
            elif config_field in ["capture_output", "auto_discover", "output_files_in_run"]:
                val = bool(val)
            settings[config_field] = val
    return settings


def _create_config(settings: dict[str, Any]) -> RairConfig:
    """Create a RairConfig from parsed settings, using defaults for missing ones."""
    config = RairConfig()
    for config_field, val in settings.items():
        setattr(config, config_field, val)
    return config


def parse_rair_config(config_data: dict[str, Any]) -> RairConfig:
    """Parse rair configuration from loaded TOML data.

    Args:
        config_data: Dictionary from TOML file

    Returns:
        RairConfig instance
    """
    rair_section = _get_rair_section(config_data)
    return _create_config(_parse_rair_section(rair_section) if rair_section is not None else {})


def _load_settings(directory: Path, config_name: Optional[str] = None) -> dict[str, Any]:
    """Load the settings given in the config file of a single directory.

    Uses .rair.toml if present, otherwise a pyproject.toml with [tool.rair] section.

    Args:
        directory: Directory to search
        config_name: Specific config file name (default: .rair.toml)

    Returns:
        Mapping of RairConfig field names to parsed values (empty without config)
    """
    config_path = find_config_file(directory, config_name)
    if config_path is None:
        config_path = find_pyproject_toml(directory)
    if config_path is None:
        return {}

    rair_section = _get_rair_section(load_toml_config(config_path))
    return _parse_rair_section(rair_section) if rair_section is not None else {}


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
    return _create_config(_load_settings(project_dir, config_name))


def _get_config_dirs(execution_dir: Path, project_dir: Path) -> list[Path]:
    """Get the directories to search for config files, from project_dir down to execution_dir."""
    resolved_execution_dir = execution_dir.resolve()
    resolved_project_dir = project_dir.resolve()

    if resolved_execution_dir == resolved_project_dir:
        return [project_dir]
    if not resolved_execution_dir.is_relative_to(resolved_project_dir):
        return [project_dir, execution_dir]

    config_dirs = [project_dir]
    for part in resolved_execution_dir.relative_to(resolved_project_dir).parts:
        config_dirs.append(config_dirs[-1] / part)
    return config_dirs


def load_hierarchical_config(
    execution_dir: Path,
    project_dir: Path,
    config_name: Optional[str] = None,
) -> RairConfig:
    """Load rair configuration with hierarchical lookup.

    Merges the config files (.rair.toml or a pyproject.toml with a [tool.rair]
    section) of all directories from project_dir down to execution_dir. A
    setting in a subdirectory overrides the same setting of its parent
    directories, settings that are not given are inherited. List values (glob
    patterns) are replaced, not concatenated.

    Args:
        execution_dir: Current working directory (highest priority)
        project_dir: Project root directory (lowest priority)
        config_name: Specific config file name (default: .rair.toml)

    Returns:
        RairConfig instance with merged configuration
    """
    settings: dict[str, Any] = {}
    for config_dir in _get_config_dirs(execution_dir, project_dir):
        settings.update(_load_settings(config_dir, config_name))
    return _create_config(settings)


def merge_config_with_cli(
    config: RairConfig,
    cli_input: Optional[list[str]],
    cli_output: Optional[list[str]],
    cli_exclude: Optional[list[str]],
    cli_archive_dir: Optional[Path],
    cli_autodata: Optional[Path] = None,
    cli_capture_output: Optional[bool] = None,
    cli_auto_discover: Optional[bool] = None,
    cli_output_files_in_run: Optional[bool] = None,
) -> RairConfig:
    """Merge file config with CLI arguments.

    CLI arguments override file configuration.

    Args:
        config: Loaded file configuration
        cli_input: CLI --input value
        cli_output: CLI --output value
        cli_exclude: CLI --exclude value
        cli_archive_dir: CLI --archive-dir value
        cli_autodata: CLI --autodata value
        cli_capture_output: CLI --capture-output/--no-capture-output value
        cli_auto_discover: CLI --auto-discover/--no-auto-discover value
        cli_output_files_in_run: CLI --output-files-in-run/--no-output-files-in-run value

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

    if cli_capture_output is not None:
        config.capture_output = cli_capture_output

    if cli_auto_discover is not None:
        config.auto_discover = cli_auto_discover

    if cli_output_files_in_run is not None:
        config.output_files_in_run = cli_output_files_in_run

    return config