"""Interactive setup dialog for rair configuration."""

import subprocess
from pathlib import Path
from typing import Optional
import typer
from typer import confirm, prompt

from .git import get_toplevel
from .config import RairConfig, load_config


def is_git_project(directory: Path) -> bool:
    """Check if directory is inside a git project."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and "true" in result.stdout.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def read_gitignore(git_dir: Path) -> list[str]:
    """Read current .gitignore entries."""
    gitignore_path = git_dir / ".gitignore"
    if gitignore_path.exists():
        return gitignore_path.read_text().splitlines()
    return []


def add_gitignore_entries(git_dir: Path, entries: list[str]) -> None:
    """Write entries to .gitignore."""
    gitignore_path = git_dir / ".gitignore"
    existing = read_gitignore(git_dir)
    new_entries = [e for e in entries if e not in existing]
    if new_entries:
        with open(gitignore_path, "a") as f:
            f.write("\n" + "\n".join(new_entries) + "\n")


def setup_interactive(
    archive_dir: Optional[str] = None,
    input_patterns: Optional[str] = None,
    output_patterns: Optional[str] = None,
    auto_discover: Optional[bool] = None,
) -> RairConfig:
    """Run interactive setup dialog.

    Args:
        archive_dir: Pre-specified archive directory (optional)
        input_patterns: Pre-specified input patterns (optional)
        output_patterns: Pre-specified output patterns (optional)
        auto_discover: Pre-specified auto-discover setting (optional)

    Returns:
        RairConfig with the configured settings
    """
    typer.echo("Welcome to rair setup!")
    typer.echo("=" * 40)

    project_dir = get_toplevel()
    is_git = is_git_project(project_dir)

    if archive_dir is None:
        typer.echo("\n1. Where should rair store archived data?")
        archive_dir = prompt(
            "Archive directory",
            default="rairarchive",
            type=str,
        )

    archive_path = Path(archive_dir) if archive_dir else Path("rairarchive")
    archive_in_git = False
    if is_git:
        try:
            archive_in_git = str(archive_path.resolve()).startswith(
                str(project_dir.resolve())
            )
        except OSError:
            archive_in_git = False

    if archive_in_git:
        typer.echo(f"\n2. The archive directory '{archive_dir}' is inside your git project.")
        if confirm(f"Add '{archive_dir}/' to .gitignore to avoid committing archives?", default=True):
            add_gitignore_entries(project_dir, [f"{archive_dir}/"])

    if input_patterns is None:
        typer.echo("\n3. What files/folders should be tracked as input data?")
        typer.echo("   (Enter glob patterns like 'data/*.csv', 'models/*.pkl', or 'data/' for directories)")
        input_patterns = prompt(
            "Input patterns (comma-separated, or press Enter for none)",
            default="",
            type=str,
        )

    input_list = [p.strip() for p in input_patterns.split(",") if p.strip()] if input_patterns else []

    if output_patterns is None:
        typer.echo("\n4. What files/folders should be tracked as output data?")
        typer.echo("   (Leave empty to auto-discover outputs, or enter glob patterns)")
        output_patterns = prompt(
            "Output patterns (comma-separated, or press Enter for auto-discovery)",
            default="",
            type=str,
        )

    output_list = [p.strip() for p in output_patterns.split(",") if p.strip()] if output_patterns else []

    if auto_discover is None:
        typer.echo("\n5. Should rair automatically discover files that changed?")
        typer.echo("   Auto-discovery tracks files based on changes before/after your script runs.")
        auto_discover = confirm("Enable auto-discovery for unspecified patterns?", default=True)

    if not auto_discover and not input_list and not output_list:
        typer.echo("\n[WARNING] Auto-discovery is disabled but no input/output patterns specified.")
        typer.echo("          No files will be tracked unless you add patterns to your config.")

    config = RairConfig(
        archive_dir=Path(archive_dir) if archive_dir else Path("rairarchive"),
        input_glob=input_list,
        output_glob=output_list,
        autodata_dir=project_dir if auto_discover else None,
        auto_discover=auto_discover,
    )

    typer.echo("\n" + "=" * 40)
    typer.echo("Setup complete! Configuration:")
    typer.echo(f"  Archive directory: {config.archive_dir}")
    typer.echo(f"  Input patterns: {config.input_glob}")
    typer.echo(f"  Output patterns: {config.output_glob}")
    typer.echo(f"  Auto-discover: {config.auto_discover}")

    return config