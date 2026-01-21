"""Core orchestration logic for rair."""

import os
import subprocess
import sys
from pathlib import Path

from .archive import create_run_info, generate_run_id
from .git import get_status
from .models import FileSnapshot, GitInfo, RunConfig, TrackedFile
from .tracking import (
    create_snapshot,
    discover_files,
    load_cache,
    save_cache,
)


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
    config: RunConfig,
) -> int:
    """Run a script with data versioning."""
    base_dir = script.resolve().parent
    original_cwd = os.getcwd()

    try:
        os.chdir(base_dir)

        cache_dir = base_dir / ".rair_cache"
        cache = load_cache(cache_dir)

        input_files = collect_files(base_dir, config.input_globs, config.exclude_globs)
        before_snapshot = create_snapshot(input_files, cache)

        git_status = get_status(cwd=base_dir)
        git_info = create_git_info(git_status)

        script_output: str | None = None
        return_code: int

        if config.capture_output:
            process = subprocess.Popen(
                [sys.executable, str(script)] + args,
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
                [sys.executable, str(script)] + args,
                cwd=str(base_dir),
            )
            return_code = result.returncode

        output_files = collect_files(base_dir, config.output_globs, config.exclude_globs)
        after_snapshot = create_snapshot(output_files, cache)

        save_cache(cache_dir, cache)

        archive_path = base_dir / config.archive_dir
        run_id = generate_run_id(archive_path)
        run_info = create_run_info(
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
    input_globs: list[str],
    output_globs: list[str],
    exclude_globs: list[str] | None = None,
    archive_dir: Path | None = None,
) -> int:
    """Simple entry point with minimal configuration."""
    config = RunConfig(
        input_globs=input_globs,
        output_globs=output_globs,
        exclude_globs=exclude_globs or [],
        archive_dir=archive_dir or Path("rairarchive"),
    )
    return run(script, args, config)