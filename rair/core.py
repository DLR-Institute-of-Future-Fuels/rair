"""Core orchestration logic for rair."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .archive import create_run_info, generate_run_id
from .git import get_status, get_tracked_files
from .models import GitInfo
from .config import RairConfig
from .script_type import get_command_args, detect_script_type
from .tracking import (
    create_snapshot,
    discover_files,
    load_cache,
    save_cache,
)
from .auto_detect import (
    get_auto_discover_candidates,
    get_file_hash_map,
    categorize_files_by_changes,
)


def should_use_auto_discovery_for_input(config: RairConfig) -> bool:
    """Check if auto-discovery should be used for input files."""
    return not config.input_glob and config.autodata_dir is not None


def should_use_auto_discovery_for_output(config: RairConfig) -> bool:
    """Check if auto-discovery should be used for output files."""
    return not config.output_glob and config.autodata_dir is not None


def collect_files(
    base_dir: Path,
    globs: list[str],
    exclude: list[str],
) -> list[Path]:
    """Collect files matching the given globs."""
    if not globs:
        return []
    return discover_files(base_dir, globs, exclude)


def create_git_info(status: dict[str, str]) -> GitInfo:
    """Create a GitInfo object from git status dict."""
    return GitInfo(
        commit_hash=status["commit_hash"],
        short_hash=status["short_hash"],
        branch=status["branch"],
        diff=status["diff"],
        diff_hash=status["diff_hash"],
        tracking_url=status["tracking_url"],
    )


def run(
    script: Path,
    args: list[str],
    config: RairConfig,
    command_override: Optional[str] = None,
) -> int:
    """Run a script with data versioning.

    Args:
        script: Path to the script file
        args: Arguments to pass to the script
        config: Configuration for data versioning
        command_override: Optional command to use instead of auto-detection
    """
    base_dir = script.resolve().parent
    original_cwd = os.getcwd()

    try:
        os.chdir(base_dir)

        cache_dir = base_dir / ".rair_cache"
        cache = load_cache(cache_dir)

        tracked_files: list[Path] = []
        before_hashes: dict[Path, str] = {}
        exclude = config.exclude_glob
        candidates: list[Path] = []

        if should_use_auto_discovery_for_input(config) or should_use_auto_discovery_for_output(config):
            tracked_files = get_tracked_files(base_dir)
            candidates = get_auto_discover_candidates(base_dir, tracked_files + exclude, config.archive_dir.absolute())
            if should_use_auto_discovery_for_output(config):
                before_hashes = get_file_hash_map(candidates)

        if should_use_auto_discovery_for_input(config):
            input_files = candidates
        else:
            input_files = collect_files(base_dir, config.input_glob, config.exclude_glob)

        before_snapshot = create_snapshot(input_files, cache)

        git_status = get_status(cwd=base_dir)
        git_info = create_git_info(git_status)

        if command_override:
            command_args = [command_override, str(script)]
        else:
            detected_type = detect_script_type(script)
            command_args = get_command_args(script, detected_type)
        full_command = command_args + args

        script_output: str | None = None
        return_code: int

        if config.capture_output:
            process = subprocess.Popen(
                full_command,
                cwd=str(base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            output_lines: list[str] = []
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                output_lines.append(line)
            process.wait()
            script_output = "".join(output_lines)
            return_code = process.returncode
        else:
            result = subprocess.run(
                full_command,
                cwd=str(base_dir),
            )
            return_code = result.returncode

        if should_use_auto_discovery_for_output(config):
            candidates = get_auto_discover_candidates(base_dir, tracked_files + exclude, config.archive_dir.absolute())
            after_hashes = get_file_hash_map(candidates)
            output_files = categorize_files_by_changes(before_hashes, after_hashes)
        else:
            output_files = collect_files(base_dir, config.output_glob, config.exclude_glob)
        
        after_snapshot = create_snapshot(output_files, cache)

        save_cache(cache_dir, cache)

        archive_path = base_dir / config.archive_dir
        run_id = generate_run_id(archive_path)
        create_run_info(
            run_id=run_id,
            script=script,
            project_dir=base_dir,
            archive_dir=archive_path,
            git_info=git_info,
            input_snapshot=before_snapshot,
            output_snapshot=after_snapshot,
            script_output=script_output,
        )

        return return_code
    finally:
        os.chdir(original_cwd)


def run_simple(
    script: Path,
    args: list[str],
    input_glob: list[str],
    output_glob: list[str],
    exclude_glob: list[str] | None = None,
    archive_dir: Path | None = None,
) -> int:
    """Simple entry point with minimal configuration."""
    config = RairConfig(
        input_glob=input_glob,
        output_glob=output_glob,
        exclude_glob=exclude_glob or [],
        archive_dir=archive_dir or Path("rairarchive"),
    )
    return run(script, args, config)