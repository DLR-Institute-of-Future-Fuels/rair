"""Git operations for rair."""

import hashlib
import subprocess
from pathlib import Path
from typing import Callable, Optional, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def _call_git_command(
    args: list[str],
    check: bool = True,
    cwd: Optional[Path] = None,
) -> str:
    """Execute a git command and return the output."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=check,
        cwd=str(cwd) if cwd else None,
    )
    return result.stdout.strip()


def get_commit_hash(cwd: Optional[Path] = None) -> str:
    """Return the full git commit hash of the current HEAD."""
    try:
        return _call_git_command(["rev-parse", "HEAD"], cwd=cwd)
    except subprocess.CalledProcessError:
        return "no-commit"


def get_short_hash(cwd: Optional[Path] = None) -> str:
    """Return the short git commit hash of the current HEAD."""
    try:
        return _call_git_command(["rev-parse", "--short", "HEAD"], cwd=cwd)
    except subprocess.CalledProcessError:
        return "no-commit"


def get_branch(cwd: Optional[Path] = None) -> str:
    """Return the current branch name."""
    try:
        return _call_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    except subprocess.CalledProcessError:
        return "unknown"


def get_diff(cwd: Optional[Path] = None) -> str:
    """Return the uncommitted changes in the working directory."""
    try:
        return _call_git_command(["diff", "HEAD"], cwd=cwd)
    except subprocess.CalledProcessError:
        return ""


def get_diff_hash(diff: str) -> str:
    """Return a short hash of the git diff."""
    if not diff:
        return ""
    return hashlib.sha256(diff.encode("utf-8")).hexdigest()[:8]


def get_tracking_url(cwd: Optional[Path] = None) -> str:
    """Return the URL of the remote tracking branch."""
    try:
        upstream = _call_git_command(
            ["rev-parse", "--symbolic-full-name", "@{u}"], cwd=cwd
        )
        remote = upstream.split("/", 1)[0]
        return _call_git_command(["remote", "get-url", remote], cwd=cwd)
    except subprocess.CalledProcessError:
        return "no-upstream"


def get_status(cwd: Optional[Path] = None) -> dict[str, str]:
    """Get all git information for a run."""
    commit_hash = get_commit_hash(cwd)
    short_hash = get_short_hash(cwd)
    branch = get_branch(cwd)
    diff = get_diff(cwd)
    diff_hash = get_diff_hash(diff)
    tracking_url = get_tracking_url(cwd)

    return {
        "commit_hash": commit_hash,
        "short_hash": short_hash,
        "branch": branch,
        "diff": diff,
        "diff_hash": diff_hash,
        "tracking_url": tracking_url,
    }