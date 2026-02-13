"""Core orchestration logic for rair."""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from .archive import create_run_info, generate_run_id, compute_combined_hash
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


def get_archive_dir_for_exclude(base_dir: Path, config: RairConfig) -> Path:
    """Get the archive directory path for exclusion in auto-discovery.

    Handles both absolute and relative paths correctly, resolving relative paths
    from the base_dir (project root) rather than the current working directory.

    Args:
        base_dir: The project directory
        config: RairConfig with archive_dir setting

    Returns:
        Resolved absolute Path to the archive directory
    """
    if config.archive_dir.is_absolute():
        return config.archive_dir.resolve()
    else:
        return (base_dir / config.archive_dir).resolve()


def should_use_auto_discovery_for_input(config: RairConfig) -> bool:
    """Check if auto-discovery should be used for input files."""
    return (config.auto_discover is not False and
            not config.input_glob and
            config.autodata_dir is not None)


def should_use_auto_discovery_for_output(config: RairConfig) -> bool:
    """Check if auto-discovery should be used for output files."""
    return (config.auto_discover is not False and
            not config.output_glob and
            config.autodata_dir is not None)


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
    script: Path | None,
    base_dir: Path,
    args: list[str],
    config: RairConfig,
    command_override: Optional[str] = None,
    execution_dir: Path | None = None,
) -> int:
    """Run a script with data versioning.

    Args:
        script: Path to the script file
        base_dir: Project root directory for file tracking and git operations
        args: Arguments to pass to the script
        config: Configuration for data versioning
        command_override: Optional command to use instead of auto-detection
        execution_dir: Directory to run the script from (defaults to base_dir)
    """
    if execution_dir is None:
        execution_dir = base_dir

    original_cwd = os.getcwd()

    try:
        os.chdir(execution_dir)

        cache_dir = base_dir / ".rair_cache"
        cache = load_cache(cache_dir)

        tracked_files: list[Path] = []
        before_hashes: dict[Path, str] = {}
        exclude = config.exclude_glob
        candidates: list[Path] = []

        if should_use_auto_discovery_for_input(config) or should_use_auto_discovery_for_output(config):
            tracked_files = get_tracked_files(base_dir)
            archive_dir_for_exclude = get_archive_dir_for_exclude(base_dir, config)
            candidates = get_auto_discover_candidates(base_dir, tracked_files + exclude, archive_dir_for_exclude)
            if should_use_auto_discovery_for_output(config):
                before_hashes = get_file_hash_map(candidates)

        if should_use_auto_discovery_for_input(config):
            input_files = candidates
        else:
            input_files = collect_files(base_dir, config.input_glob, config.exclude_glob)

        before_snapshot = create_snapshot(input_files, cache)

        git_status = get_status(cwd=base_dir)
        git_info = create_git_info(git_status)

        input_file_hashes = [file.hash for file in before_snapshot.files.values()]
        full_hash, short_hash = compute_combined_hash(
            git_info.commit_hash,
            git_info.diff_hash,
            input_file_hashes
        )

        if command_override:
            if isinstance(script, Path):
                command_args = [command_override, str(script)]
            else:
                command_args = [command_override]
        else:
            assert script, 'A script or executable needs to be specified'
            detected_type = detect_script_type(script)
            command_args = get_command_args(script, detected_type)
        full_command = command_args + args

        script_output: str | None = None
        return_code: int

        # Time the script execution
        start_time = time.time()
        
        if config.capture_output is not False:
            process = subprocess.Popen(
                full_command,
                cwd=str(execution_dir),
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
                cwd=str(execution_dir),
            )
            return_code = result.returncode
            
        end_time = time.time()
        execution_time = end_time - start_time

        if should_use_auto_discovery_for_output(config):
            archive_dir_for_exclude = get_archive_dir_for_exclude(base_dir, config)
            candidates = get_auto_discover_candidates(base_dir, tracked_files + exclude, archive_dir_for_exclude)
            after_hashes = get_file_hash_map(candidates)
            output_files = categorize_files_by_changes(before_hashes, after_hashes)
        else:
            output_files = collect_files(base_dir, config.output_glob, config.exclude_glob)
        
        after_snapshot = create_snapshot(output_files, cache)

        save_cache(cache_dir, cache)

        archive_path = base_dir / config.archive_dir
        run_id = generate_run_id(cache_dir, short_hash)
        create_run_info(
            run_id=run_id,
            command=full_command,
            project_dir=base_dir,
            archive_dir=archive_path,
            git_info=git_info,
            input_snapshot=before_snapshot,
            output_snapshot=after_snapshot,
            script_output=script_output,
            combined_hash=full_hash,
            execution_time=execution_time,
            output_files_in_run=config.output_files_in_run,
        )

        return return_code
    finally:
        os.chdir(original_cwd)