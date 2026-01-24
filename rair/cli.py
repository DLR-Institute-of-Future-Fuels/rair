"""CLI for rair using Typer."""

from pathlib import Path
from typing import Optional

import typer
from typer import Argument, Option

from .config import load_config, merge_config_with_cli, RairConfig
from .core import run
from .config import RairConfig

app = typer.Typer(
    add_completion=False,
    help="Rair - Simple data versioning for Python experiments",
)


@app.command()
def main(
    script: Path = Argument(
        ...,
        help="Python script to run",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
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
    capture_output: bool = Option(
        default=True,
        help="Capture and save script output to out.txt",
    ),
) -> None:
    """Run a Python script with data versioning."""
    project_dir = script.resolve().parent

    file_config = load_config(project_dir, config.name if config else None)

    merged_config = merge_config_with_cli(
        file_config,
        input,
        output,
        exclude,
        archive_dir,
    )

    run_config = RairConfig(
        input_glob=merged_config.input_glob,
        output_glob=merged_config.output_glob,
        exclude_glob=merged_config.exclude_glob,
        archive_dir=merged_config.archive_dir,
        capture_output=capture_output,
    )

    exit_code = run(script, args, run_config)

    raise typer.Exit(code=exit_code)


def entry_point() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()