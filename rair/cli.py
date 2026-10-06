"""CLI for rair using Typer."""

import os
import shlex
from pathlib import Path
from typing import Optional

import typer
from typer import Argument, Option

from .config import (
    load_hierarchical_config,
    load_toml_config,
    merge_config_with_cli,
    parse_rair_config,
    RairConfig,
)
from .core import run
from .cli_parser import is_script_extension
from .git import get_toplevel
from .setup import setup_interactive

app = typer.Typer(
    add_completion=False,
    help="Rair - Simple data versioning for Python experiments",
)


# Unknown options are passed on to the script, so that `rair myscript.py --lr 0.1` works
@app.command(context_settings={"ignore_unknown_options": True})
def main(
    script_or_command: Optional[str] = Argument(
        default=None,
        help="Script path (with extension) or command (python, bash, make, etc.)",
    ),
    args: list[str] = Argument(
        default=[],
        help="Arguments to pass to the script",
    ),
    config: Optional[Path] = Option(
        default=None,
        help="Path to config file",
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    input: Optional[list[str]] = Option(
        default=None,
        help="Glob pattern for input files to track",
    ),
    output: Optional[list[str]] = Option(
        default=None,
        help="Glob pattern for output files to track",
    ),
    exclude: Optional[list[str]] = Option(
        default=None,
        help="Glob pattern to exclude from tracking",
    ),
    archive_dir: Optional[Path] = Option(
        default=None,
        help="Directory for archive data (default: rairarchive)",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    autodata: Optional[Path] = Option(
        default=None,
        help="Directory for auto-discovering input/output files",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    capture_output: Optional[bool] = Option(
        default=None,
        help="Write console output to out.txt (default: on)",
    ),
    auto_discover: Optional[bool] = Option(
        default=None,
        help="Enable auto-discovery when --input/--output not specified (default: on)",
    ),
    output_files_in_run: Optional[bool] = Option(
        default=None,
        help="Create hardlinks to output files in the run folder (default: on)",
    ),
    comment: Optional[str] = Option(
        default="",
        help="Add a comment to info.md and run.json",
    ),
    setup: bool = Option(
        False,
        "--setup",
        help="Run interactive setup dialog",
    ),
) -> None:
    """Run a script with data versioning.

    Examples:
        rair myscript.py arg1 arg2
        rair python mymodel.py arg1 arg2
        rair make --all
        rair --setup

    Options unknown to rair are passed on to the script. Use "--" to pass
    options that rair knows itself: rair myscript.py -- --input file.txt
    """

    execution_dir = Path.cwd()

    if setup:
        setup_interactive(
            auto_discover=auto_discover,
            output_files_in_run=output_files_in_run,
        )
        raise typer.Exit(0)

    if config is not None and not config.is_file():
        typer.echo(f"Error: Config file not found: {config}", err=True)
        raise typer.Exit(1)

    if script_or_command is None:
        file_config = _load_file_config(execution_dir, get_toplevel(), config)
        if file_config.default_command:
            # The default command may contain arguments, e.g. "python train.py --fast"
            command_parts = shlex.split(file_config.default_command, posix=os.name != "nt")
            script_or_command = command_parts[0]
            args = command_parts[1:] + args
        else:
            typer.echo("Error: No script or command specified. Use --help for usage information.")
            raise typer.Exit(1)

    if is_script_extension(script_or_command):
        command = None
        script = Path(script_or_command)
        script_args = args
    else:
        command = script_or_command
        if not args:
            script = None
        else:
            script = Path(args[0])
        script_args = args[1:]

    # The first argument of a command is not necessarily a path to a script
    if script is not None and script.parent.is_dir():
        project_dir = get_toplevel(script.parent)
    else:
        project_dir = get_toplevel()

    file_config = _load_file_config(execution_dir, project_dir, config)

    run_config = merge_config_with_cli(
        file_config,
        cli_input=input,
        cli_output=output,
        cli_exclude=exclude,
        cli_archive_dir=archive_dir,
        cli_autodata=autodata,
        cli_capture_output=capture_output,
        cli_auto_discover=auto_discover,
        cli_output_files_in_run=output_files_in_run,
    )
    if run_config.autodata_dir is None:
        run_config.autodata_dir = project_dir
    run_config.comment = comment

    exit_code = run(script, project_dir, script_args, run_config, command, execution_dir)

    raise typer.Exit(code=exit_code)


def _load_file_config(execution_dir: Path, project_dir: Path, config: Optional[Path]) -> RairConfig:
    """Load the file configuration, preferring an explicitly given config file."""
    if config is not None:
        return parse_rair_config(load_toml_config(config))
    return load_hierarchical_config(execution_dir, project_dir)


def entry_point() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()