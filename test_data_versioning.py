import subprocess
import time
import hashlib
import os


def stable_hash(s: str, lengths: int = 0) -> str:
    if lengths:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:lengths]
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def call_command(command: list[str]) -> str:
    return subprocess.check_output(
        command,
        stderr=subprocess.DEVNULL
    ).decode("ascii").strip()


def get_git_short_hash():
    """Return short git hash of the current HEAD."""
    return call_command(["git", "rev-parse", "--short", "HEAD"])


def get_branch_name():
    """Return short git hash of the current HEAD."""
    try:
        return call_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    except subprocess.CalledProcessError:
        return "unknown"


def get_git_hash():
    """Return short git hash of the current HEAD."""
    return call_command(["git", "rev-parse", "HEAD"])


def get_git_diff():
    """Return changes in the working directory compared to HEAD."""
    return call_command(["git", "diff", "HEAD"])


def get_directory_name(git_hash: str, git_diff_hash: str) -> str:
    """Return name composed of date, time and git hash and hash of git diff."""
    date_str = time.strftime("%Y%m%d-%H%M%S")
    if git_diff_hash:
        # There are uncommitted changes
        return f"{date_str}_{git_hash}_{git_diff_hash}"
    else:
        return f"{date_str}_{git_hash}"


def get_tracking_branch_url():
    try:
        upstream = call_command(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        remote = upstream.split("/", 1)[0]
        return call_command(["git", "remote", "get-url", remote])
    except Exception:
        return "no-upstream"


def get_result_directory_name(result_path: str = 'results') -> str:
    """Return result directory name based on git state and current time."""
    git_hash = get_git_hash()
    git_short_hash = get_git_short_hash()
    git_diff = get_git_diff()
    git_diff_hash = stable_hash(git_diff, 4) if git_diff else ""
    path = result_path + "/" + get_directory_name(git_short_hash, git_diff_hash) + "/"
    tracking_branch_url = get_tracking_branch_url()

    if tracking_branch_url.startswith('https://gitlab.dlr.de/'):
        gitlab_link = tracking_branch_url.replace('.git', '/-/tree/' + git_hash)
    else:
        gitlab_link = None

    # Create the directory if it does not exist
    os.makedirs(path, exist_ok=True)
    
    with open(path + "git_diff.patch", "w") as f:
        f.write(git_diff)

    with open(path + "info.md", "w") as f:
        f.write(f"# Data information\n\n")
        f.write(f"- Run time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if gitlab_link:
            f.write(f"- Git hash: [{git_hash}]({gitlab_link})\n")
        else:
            f.write(f"- Git hash: `{git_hash}`\n")
        f.write(f"- Git hash short: `{git_short_hash}`\n")
        f.write(f"- Branch name: `{get_branch_name()}`\n")
        f.write(f"- Tracking branch URL: `{tracking_branch_url}`\n")
        if git_diff_hash:
            f.write(f"- Uncommitted changes:\n\n")
            f.write(f"```diff\n{git_diff}\n```\n")	
        else:
            f.write(f"- No uncommitted changes\n")

    return path
