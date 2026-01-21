"""Archive management for rair."""

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


def generate_run_id(git_info: GitInfo) -> str:
    """Generate a unique run ID from git info and timestamp."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    diff_suffix = f"_{git_info.diff_hash}" if git_info.diff_hash else ""
    return f"{timestamp}_{git_info.short_hash}{diff_suffix}"


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


def write_run_info(
    run_dir: Path,
    script: Path,
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

    with open(run_dir / "info.md", "w") as f:
        f.write("# Run Information\n\n")
        f.write(f"- Run time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- Script: `{script}`\n\n")

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

            f.write("\n## Restore Code\n\n")
            f.write("To restore the code state for this run, run:\n\n")
            f.write("```bash\n")
            f.write(f"git checkout {git_info.commit_hash}\n")
            f.write(f"git apply {diff_path}\n")
            f.write("```\n")

        f.write("\n## Input Files\n\n")
        for tracked in sorted(input_files, key=lambda x: str(x.path)):
            path_str = str(tracked.path)
            archived_path = archived_files.get(path_str)
            if archived_path:
                f.write(f"- `{tracked.path}` -> `{archived_path}` (hash: `{tracked.hash_prefix}`)\n")
            else:
                f.write(f"- `{tracked.path}` (hash: `{tracked.hash_prefix}`)\n")

        f.write("\n## Output Files\n\n")
        for tracked in sorted(output_files, key=lambda x: str(x.path)):
            path_str = str(tracked.path)
            archived_path = archived_files.get(path_str)
            if archived_path:
                f.write(f"- `{tracked.path}` -> `{archived_path}` (hash: `{tracked.hash_prefix}`)\n")
            else:
                f.write(f"- `{tracked.path}` (hash: `{tracked.hash_prefix}`)\n")


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
    archive_dir: Path,
    git_info: GitInfo,
    input_snapshot: FileSnapshot,
    output_snapshot: FileSnapshot,
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
        git_info,
        list(input_snapshot.files.values()),
        list(output_snapshot.files.values()),
        archived_files,
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