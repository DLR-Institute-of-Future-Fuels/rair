"""Archive management for rair."""

import json
import shutil
import time
from pathlib import Path

from .models import FileSnapshot, GitInfo, RunConfig, RunInfo, TrackedFile


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_unique_data_path(data_dir: Path, file_hash: str, original_name: str) -> Path:
    """Get the path for a unique data file, deduplicated by hash."""
    data_dir.mkdir(parents=True, exist_ok=True)
    safe_name = original_name.replace("/", "_").replace("\\", "_")
    unique_name = f"{file_hash}_{safe_name}"
    return data_dir / unique_name


def copy_to_data_archive(
    file_path: Path,
    data_dir: Path,
) -> Path:
    """Copy a file to the data archive, deduplicated by hash."""
    file_hash = compute_file_hash(file_path)
    dest_path = get_unique_data_path(data_dir, file_hash, file_path.name)

    if not dest_path.exists():
        shutil.copy2(file_path, dest_path)

    return dest_path


def get_run_counter_path(archive_dir: Path) -> Path:
    """Get the path to the run counter file."""
    runs_dir = archive_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir / ".run_counter.json"


def get_next_run_number(archive_dir: Path) -> int:
    """Get the next run number for today, initializing if needed."""
    counter_path = get_run_counter_path(archive_dir)
    today = time.strftime("%Y%m%d")

    if counter_path.exists():
        try:
            with open(counter_path, "r") as f:
                data: dict[str, object] = json.load(f)
            if data.get("date") == today:
                number_val = data.get("number")
                if isinstance(number_val, (int, float)):
                    run_number = int(number_val) + 1
                else:
                    run_number = 1
            else:
                run_number = 1
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            run_number = 1
    else:
        run_number = 1

    with open(counter_path, "w") as f:
        json.dump({"date": today, "number": run_number}, f)

    return run_number


def generate_run_id(archive_dir: Path) -> str:
    """Generate a unique run ID with date and incrementing number."""
    today = time.strftime("%Y%m%d")
    run_number = get_next_run_number(archive_dir)
    return f"{today}-{run_number:03d}"


def create_run_directory(archive_dir: Path, run_id: str) -> Path:
    """Create the run directory."""
    run_dir = archive_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def get_gitlab_link(tracking_url: str, commit_hash: str) -> str | None:
    """Generate a GitLab link if applicable."""
    if tracking_url.startswith("https://gitlab.dlr.de/"):
        return tracking_url.rstrip(".git") + "/-/tree/" + commit_hash
    return None


def _make_relative_path(project_dir: Path, archive_dir: Path, path: Path) -> Path:
    """Convert absolute path to relative if archive_dir is within project_dir."""
    try:
        if archive_dir.is_relative_to(project_dir):
            return path.relative_to(project_dir)
    except ValueError:
        pass
    return path


def _format_file_for_display(
    project_dir: Path,
    archive_dir: Path,
    tracked: TrackedFile,
    archived_path: Path | None,
) -> str:
    """Format a file entry for display in info.md."""
    display_path = _make_relative_path(project_dir, archive_dir, tracked.path)
    if archived_path:
        display_archived = _make_relative_path(project_dir, archive_dir, archived_path)
        return f"`{display_path}` -> `{display_archived}` (hash: `{tracked.hash_prefix}`)"
    return f"`{display_path}` (hash: `{tracked.hash_prefix}`)"


def write_run_info(
    run_dir: Path,
    script: Path,
    project_dir: Path,
    archive_dir: Path,
    git_info: GitInfo,
    input_files: list[TrackedFile],
    output_files: list[TrackedFile],
    archived_files: dict[str, Path],
) -> None:
    """Write the info.md file for a run."""
    gitlab_link = get_gitlab_link(git_info.tracking_url, git_info.commit_hash)

    diff_path = run_dir / "git_diff.patch"

    if git_info.diff:
        with open(diff_path, "w") as f:
            f.write(git_info.diff)

    display_script = _make_relative_path(project_dir, archive_dir, script)

    with open(run_dir / "info.md", "w") as f:
        f.write("# Run Information\n\n")
        f.write(f"- Run time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- Script: `{display_script}`\n\n")

        f.write("## Git Information\n\n")
        if gitlab_link:
            f.write(f"- Commit: [{git_info.commit_hash[:8]}]({gitlab_link})\n")
        else:
            f.write(f"- Commit: `{git_info.commit_hash}`\n")
        f.write(f"- Short hash: `{git_info.short_hash}`\n")
        f.write(f"- Branch: `{git_info.branch}`\n")
        f.write(f"- Tracking URL: `{git_info.tracking_url}`\n")

        if git_info.diff:
            f.write("\n## Uncommitted Changes\n\n")
            f.write("```diff\n")
            f.write(git_info.diff)
            f.write("\n```\n")

            diff_path_display = _make_relative_path(project_dir, archive_dir, diff_path)
            f.write("\n## Restore Code\n\n")
            f.write("To restore the code state for this run, run:\n\n")
            f.write("```bash\n")
            f.write(f"git checkout {git_info.commit_hash}\n")
            f.write(f"git apply {diff_path_display}\n")
            f.write("```\n")

        f.write("\n## Input Files\n\n")
        for tracked in sorted(input_files, key=lambda x: str(x.path)):
            path_str = str(tracked.path)
            archived_path = archived_files.get(path_str)
            f.write(f"- {_format_file_for_display(project_dir, archive_dir, tracked, archived_path)}\n")

        f.write("\n## Output Files\n\n")
        for tracked in sorted(output_files, key=lambda x: str(x.path)):
            path_str = str(tracked.path)
            archived_path = archived_files.get(path_str)
            f.write(f"- {_format_file_for_display(project_dir, archive_dir, tracked, archived_path)}\n")


def _format_file_for_json(
    project_dir: Path,
    archive_dir: Path,
    tracked: TrackedFile,
    archived_path: Path | None,
) -> dict:
    """Format a file entry for run.json."""
    return {
        "path": str(_make_relative_path(project_dir, archive_dir, tracked.path)),
        "hash": tracked.hash,
        "hash_prefix": tracked.hash_prefix,
        "archived_path": str(_make_relative_path(project_dir, archive_dir, archived_path)) if archived_path else None,
    }


def write_run_json(
    run_dir: Path,
    script: Path,
    project_dir: Path,
    archive_dir: Path,
    git_info: GitInfo,
    input_files: list[TrackedFile],
    output_files: list[TrackedFile],
    archived_files: dict[str, Path],
    has_output: bool = False,
) -> None:
    """Write the run.json file for a run."""
    run_data = {
        "run_id": run_dir.name,
        "run_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "script": str(_make_relative_path(project_dir, archive_dir, script)),
        "git": {
            "commit_hash": git_info.commit_hash,
            "short_hash": git_info.short_hash,
            "branch": git_info.branch,
            "tracking_url": git_info.tracking_url,
            "diff_hash": git_info.diff_hash,
            "has_diff": bool(git_info.diff),
        },
        "input_files": [
            _format_file_for_json(project_dir, archive_dir, f, archived_files.get(str(f.path)))
            for f in sorted(input_files, key=lambda x: str(x.path))
        ],
        "output_files": [
            _format_file_for_json(project_dir, archive_dir, f, archived_files.get(str(f.path)))
            for f in sorted(output_files, key=lambda x: str(x.path))
        ],
        "has_output": has_output,
    }

    with open(run_dir / "run.json", "w") as f:
        json.dump(run_data, f, indent=2)


def save_script_output(run_dir: Path, output: str) -> None:
    """Save script output to out.txt in run directory."""
    if not output:
        return
    output_file = run_dir / "out.txt"
    output_file.write_text(output, encoding="utf-8")


def archive_files(
    snapshot: FileSnapshot,
    data_dir: Path,
) -> dict[str, Path]:
    """Archive files from a snapshot to the data directory."""
    archived: dict[str, Path] = {}
    for path_str, tracked in snapshot.files.items():
        src_path = tracked.path
        dest_path = copy_to_data_archive(src_path, data_dir)
        archived[path_str] = dest_path
    return archived


def create_run_info(
    run_id: str,
    script: Path,
    project_dir: Path,
    archive_dir: Path,
    git_info: GitInfo,
    input_snapshot: FileSnapshot,
    output_snapshot: FileSnapshot,
    script_output: str | None = None,
) -> RunInfo:
    """Create a complete run with all data archived and info written."""
    run_dir = create_run_directory(archive_dir, run_id)
    data_dir = archive_dir / "data"
    archived_input = archive_files(input_snapshot, data_dir)
    archived_output = archive_files(output_snapshot, data_dir)
    archived_files = {**archived_input, **archived_output}

    write_run_info(
        run_dir,
        script,
        project_dir,
        archive_dir,
        git_info,
        list(input_snapshot.files.values()),
        list(output_snapshot.files.values()),
        archived_files,
    )

    has_output = script_output is not None and script_output != ""
    if has_output:
        assert script_output is not None
        save_script_output(run_dir, script_output)

    write_run_json(
        run_dir,
        script,
        project_dir,
        archive_dir,
        git_info,
        list(input_snapshot.files.values()),
        list(output_snapshot.files.values()),
        archived_files,
        has_output=has_output,
    )

    return RunInfo(
        run_id=run_id,
        git_info=git_info,
        script=script,
        archive_dir=run_dir,
        run_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        input_files=list(input_snapshot.files.keys()),
        output_files=list(output_snapshot.files.keys()),
    )