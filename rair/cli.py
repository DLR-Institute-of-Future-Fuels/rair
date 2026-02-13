"""CLI for rair using Typer."""

from pathlib import Path
from typing import Optional

import typer
from typer import Argument, Option

from .config import load_hierarchical_config, merge_config_with_cli, RairConfig
from .core import run
from .cli_parser import is_script_extension
from .git import get_toplevel
from .setup import setup_interactive

app = typer.Typer(
    add_completion=False,
    help="Rair - Simple data versioning for Python experiments",
)


@app.command()
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
        help="Directory for archive data",
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
        help="Capture and save script output to out.txt",
    ),
    auto_discover: Optional[bool] = Option(
        default=None,
        help="Enable auto-discovery when --input/--output not specified",
    ),
    output_files_in_run: Optional[bool] = Option(
        default=None,
        help="Create hardlinks to output files in the run folder",
    ),
    setup: bool = Option(
        default=False,
        help="Run interactive setup dialog",
    ),
) -> None:
    """Run a script with data versioning.

    Examples:
        rair myscript.py arg1 arg2
        rair python mymodel.py arg1 arg2
        rair make --all
        rair --setup
    """

    execution_dir = Path.cwd()

    if setup:
        setup_interactive(
            auto_discover=auto_discover,
            output_files_in_run=output_files_in_run,
        )
        raise typer.Exit(0)

    if script_or_command is None:
        project_dir = get_toplevel()
        file_config = load_hierarchical_config(execution_dir, project_dir, config.name if config else None)
        if file_config.default_command:
            script_or_command = file_config.default_command
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

    project_dir = get_toplevel(script.parent) if script else get_toplevel()

    file_config = load_hierarchical_config(execution_dir, project_dir, config.name if config else None)

    merged_config = merge_config_with_cli(
        file_config,
        input,
        output,
        exclude,
        archive_dir,
        autodata if autodata is not None else project_dir,
        auto_discover,
        output_files_in_run,
    )

    run_config = RairConfig(
        input_glob=merged_config.input_glob,
        output_glob=merged_config.output_glob,
        exclude_glob=merged_config.exclude_glob,
        archive_dir=merged_config.archive_dir,
        autodata_dir=merged_config.autodata_dir,
        capture_output=capture_output,
        auto_discover=merged_config.auto_discover,
        output_files_in_run=merged_config.output_files_in_run,
        default_command=merged_config.default_command,
    )

    exit_code = run(script, project_dir, script_args, run_config, command, execution_dir)

    raise typer.Exit(code=exit_code)


def entry_point() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()