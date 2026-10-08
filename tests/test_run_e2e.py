"""End-to-end tests running real scripts in a real git repository."""

import json
import subprocess
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rair.cli import app

SCRIPT = """import sys

print("output of model", sys.argv[1:])
p1 = 5.9

with open("result.txt", "w") as f:
    f.write(f"result = {p1} {sys.argv[1:]}\\n")
"""


def git(project_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=project_dir, check=True, capture_output=True, text=True
    )
    return result.stdout


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git project with a committed script that has uncommitted changes."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    # Write bytes to get LF line endings on all platforms
    (project_dir / "model.py").write_bytes(SCRIPT.encode())

    git(project_dir, "init")
    git(project_dir, "config", "user.email", "test@test.com")
    git(project_dir, "config", "user.name", "Test User")
    git(project_dir, "config", "core.autocrlf", "false")
    git(project_dir, "add", ".")
    git(project_dir, "commit", "-m", "initial")

    (project_dir / "model.py").write_bytes(SCRIPT.replace("p1 = 5.9", "p1 = 7.1").encode())

    monkeypatch.chdir(project_dir)
    return project_dir


def run_rair(project_dir: Path, *args: str, archive: str = "rairarchive") -> Path:
    """Run rair and return the directory of the created run."""
    runs_dir = project_dir / archive / "runs"
    before = set(runs_dir.iterdir()) if runs_dir.exists() else set()

    result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output

    new_runs = set(runs_dir.iterdir()) - before
    assert len(new_runs) == 1
    return new_runs.pop()


def load_run(run_dir: Path) -> dict:
    return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))


class TestRunContent:
    def test_default_run(self, project: Path):
        run_dir = run_rair(project, "model.py")

        assert sorted(p.name for p in run_dir.iterdir()) == [
            "git_diff.patch", "info.md", "out.txt", "result.txt", "run.json",
        ]
        assert "output of model" in (run_dir / "out.txt").read_text(encoding="utf-8")
        assert (run_dir / "result.txt").read_text() == "result = 7.1 []\n"

        run_data = load_run(run_dir)
        assert run_data["command"] == ["python", "model.py"]
        assert run_data["git"]["has_diff"] is True
        assert run_data["has_output"] is True
        assert run_data["input_files"] == []
        assert [f["path"] for f in run_data["output_files"]] == ["result.txt"]
        archived_path = project / run_data["output_files"][0]["archived_path"]
        assert archived_path.parent == project / "rairarchive" / "data"
        assert archived_path.read_text() == "result = 7.1 []\n"

        info = (run_dir / "info.md").read_text(encoding="utf-8")
        assert "- Command: `python model.py`" in info
        assert f"- Run hash: `{run_data['combined_hash']}`" in info
        assert "in model.py:\np1 = 7.1" in info
        assert "## Output Files" in info
        assert run_dir.name.endswith(run_data["combined_hash"][:8])

    def test_comment_is_stored(self, project: Path):
        run_dir = run_rair(project, "--comment", "experiment 1", "model.py")

        assert load_run(run_dir)["comment"] == "experiment 1"
        assert "- Comment: experiment 1" in (run_dir / "info.md").read_text(encoding="utf-8")

    def test_script_arguments_and_options(self, project: Path):
        run_dir = run_rair(project, "model.py", "arg1", "--lr", "0.1")

        assert load_run(run_dir)["command"] == ["python", "model.py", "arg1", "--lr", "0.1"]
        assert (project / "result.txt").read_text() == "result = 7.1 ['arg1', '--lr', '0.1']\n"

    def test_start_time_is_start_of_execution(self, project: Path):
        (project / "model.py").write_text("import time\ntime.sleep(2.5)\n")
        before = time.time()
        run_dir = run_rair(project, "model.py")

        run_data = load_run(run_dir)
        timestamp = time.mktime(time.strptime(run_data["run_timestamp"], "%Y-%m-%dT%H:%M:%S"))
        assert run_data["execution_time"] >= 2.5
        # The timestamp has a resolution of one second
        assert before - 1 <= timestamp <= before + 1.5

    def test_failing_script_returns_exit_code_and_is_archived(self, project: Path):
        (project / "model.py").write_text("import sys\nprint('failing')\nsys.exit(3)\n")
        result = CliRunner().invoke(app, ["model.py"])

        assert result.exit_code == 3
        run_dirs = list((project / "rairarchive" / "runs").iterdir())
        assert len(run_dirs) == 1
        assert "failing" in (run_dirs[0] / "out.txt").read_text(encoding="utf-8")

    def test_unknown_command_reports_error(self, project: Path):
        result = CliRunner().invoke(app, ["rair-command-that-does-not-exist", "model.py"])

        assert result.exit_code == 127
        assert not isinstance(result.exception, FileNotFoundError)
        assert not (project / "rairarchive").exists()


class TestRunHash:
    def test_same_state_gives_same_hash(self, project: Path):
        hash1 = load_run(run_rair(project, "--no-auto-discover", "model.py"))["combined_hash"]
        hash2 = load_run(run_rair(project, "--no-auto-discover", "model.py"))["combined_hash"]
        assert hash1 == hash2

    def test_arguments_change_hash(self, project: Path):
        hash1 = load_run(run_rair(project, "--no-auto-discover", "model.py"))["combined_hash"]
        hash2 = load_run(run_rair(project, "--no-auto-discover", "model.py", "arg1"))["combined_hash"]
        assert hash1 != hash2

    def test_code_change_changes_hash(self, project: Path):
        hash1 = load_run(run_rair(project, "--no-auto-discover", "model.py"))["combined_hash"]
        (project / "model.py").write_bytes(SCRIPT.replace("p1 = 5.9", "p1 = 8.2").encode())
        hash2 = load_run(run_rair(project, "--no-auto-discover", "model.py"))["combined_hash"]
        assert hash1 != hash2

    def test_input_data_change_changes_hash(self, project: Path):
        (project / "input.csv").write_text("1,2,3\n")
        hash1 = load_run(run_rair(project, "--output", "result.txt", "model.py"))["combined_hash"]
        (project / "input.csv").write_text("4,5,6\n")
        hash2 = load_run(run_rair(project, "--output", "result.txt", "model.py"))["combined_hash"]
        assert hash1 != hash2


class TestFlags:
    def test_no_capture_output(self, project: Path):
        run_dir = run_rair(project, "--no-capture-output", "model.py")

        assert not (run_dir / "out.txt").exists()
        run_data = load_run(run_dir)
        assert run_data["has_output"] is False
        # Auto-discovery and hardlinks are not affected
        assert [f["path"] for f in run_data["output_files"]] == ["result.txt"]
        assert (run_dir / "result.txt").exists()

    def test_no_auto_discover(self, project: Path):
        (project / "input.csv").write_text("1,2,3\n")
        run_dir = run_rair(project, "--no-auto-discover", "model.py")

        run_data = load_run(run_dir)
        assert run_data["input_files"] == []
        assert run_data["output_files"] == []
        # Capturing the output is not affected
        assert (run_dir / "out.txt").exists()

    def test_no_output_files_in_run(self, project: Path):
        run_dir = run_rair(project, "--no-output-files-in-run", "model.py")

        assert not (run_dir / "result.txt").exists()
        run_data = load_run(run_dir)
        # The output file is still discovered and archived
        assert [f["path"] for f in run_data["output_files"]] == ["result.txt"]
        assert (project / run_data["output_files"][0]["archived_path"]).exists()

    def test_exclude_does_not_print_debug_output(self, project: Path):
        (project / "junk.tmp").write_text("junk")
        result = CliRunner().invoke(app, ["--exclude", "*.tmp", "model.py"])

        assert result.exit_code == 0, result.output
        assert "junk.tmp" not in result.output

    def test_exclude_with_auto_discovery(self, project: Path):
        (project / "junk.tmp").write_text("junk")
        (project / "input.csv").write_text("1,2,3\n")
        run_dir = run_rair(project, "--exclude", "*.tmp", "model.py")

        assert [f["path"] for f in load_run(run_dir)["input_files"]] == ["input.csv"]

    def test_autodata_restricts_auto_discovery(self, project: Path):
        (project / "data").mkdir()
        (project / "data" / "input.csv").write_text("1,2,3\n")
        (project / "other.csv").write_text("4,5,6\n")
        (project / "model.py").write_text(
            "open('result.txt', 'w').write('a')\nopen('data/result.txt', 'w').write('b')\n"
        )
        run_dir = run_rair(project, "--autodata", "data", "model.py")

        run_data = load_run(run_dir)
        assert [f["path"] for f in run_data["input_files"]] == ["data/input.csv"]
        assert [f["path"] for f in run_data["output_files"]] == ["data/result.txt"]

    def test_autodata_dir_from_config_file(self, project: Path):
        (project / ".rair.toml").write_text('[rair]\nautodata_dir = "data"\n')
        (project / "data").mkdir()
        (project / "data" / "input.csv").write_text("1,2,3\n")
        (project / "other.csv").write_text("4,5,6\n")
        run_dir = run_rair(project, "model.py")

        run_data = load_run(run_dir)
        assert [f["path"] for f in run_data["input_files"]] == ["data/input.csv"]
        assert run_data["output_files"] == []

    def test_git_tracked_files_are_no_input_files(self, project: Path):
        run_dir = run_rair(project, "model.py")
        assert load_run(run_dir)["input_files"] == []

    def test_archive_is_not_tracked_as_input(self, project: Path):
        run_rair(project, "model.py")
        run_dir = run_rair(project, "model.py")

        run_data = load_run(run_dir)
        paths = [f["path"] for f in run_data["input_files"] + run_data["output_files"]]
        assert not [p for p in paths if p.startswith("rairarchive")]


class TestConfigFiles:
    def test_readme_rair_toml_example(self, project: Path):
        """The example from the README must be parsed as documented."""
        (project / ".rair.toml").write_text(
            '[rair]\n'
            'archive_dir = "myarchive"\n'
            'input_glob = ["data/*.csv", "cache/*.pkl"]\n'
            'output_glob = ["result*.txt", "logs/*.txt"]\n'
            'capture_output = false\n'
            'output_files_in_run = false\n'
            'default_command = "python model.py"\n'
        )
        (project / "data").mkdir()
        (project / "data" / "input.csv").write_text("1,2,3\n")
        run_dir = run_rair(project, archive="myarchive")

        assert sorted(p.name for p in run_dir.iterdir()) == ["git_diff.patch", "info.md", "run.json"]
        run_data = load_run(run_dir)
        assert run_data["command"] == ["python", "model.py"]
        assert [f["path"] for f in run_data["input_files"]] == ["data/input.csv"]
        assert [f["path"] for f in run_data["output_files"]] == ["result.txt"]

    def test_config_in_subdirectory_is_merged_with_project_config(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (project / ".rair.toml").write_text(
            '[rair]\narchive_dir = "project_archive"\ncapture_output = false\n'
        )
        experiments = project / "experiments"
        experiments.mkdir()
        (experiments / ".rair.toml").write_text('[rair]\narchive_dir = "local_archive"\n')
        (experiments / "train.py").write_text("print('train')\n")
        monkeypatch.chdir(experiments)

        run_dir = run_rair(project, "train.py", archive="local_archive")
        assert load_run(run_dir)["command"] == ["python", "train.py"]
        # archive_dir is overridden by the local config
        assert not (project / "project_archive").exists()
        # capture_output is inherited from the project config
        assert not (run_dir / "out.txt").exists()

    def test_pyproject_without_rair_section_does_not_shadow_project_config(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (project / ".rair.toml").write_text('[rair]\narchive_dir = "project_archive"\n')
        package = project / "package"
        package.mkdir()
        (package / "pyproject.toml").write_text('[project]\nname = "package"\n')
        (package / "train.py").write_text("print('train')\n")
        monkeypatch.chdir(package)

        run_rair(project, "train.py", archive="project_archive")
        assert not (project / "rairarchive").exists()


class TestRestoreCode:
    def test_stored_patch_restores_code(self, project: Path):
        """The commands from the "Restore Code" section must reproduce the code."""
        modified_code = (project / "model.py").read_bytes()
        run_dir = run_rair(project, "model.py")

        patch_path = run_dir / "git_diff.patch"
        assert b"\r\n" not in patch_path.read_bytes()
        info = (run_dir / "info.md").read_text(encoding="utf-8")
        commit_hash = load_run(run_dir)["git"]["commit_hash"]
        assert f"git checkout {commit_hash}\n" in info
        assert f'git apply "rairarchive/runs/{run_dir.name}/git_diff.patch"\n' in info

        git(project, "checkout", "--", "model.py")
        assert (project / "model.py").read_bytes() != modified_code
        git(project, "apply", f"rairarchive/runs/{run_dir.name}/git_diff.patch")
        assert (project / "model.py").read_bytes() == modified_code

    def test_patch_with_non_ascii_characters(self, project: Path):
        modified_code = SCRIPT.replace("p1 = 5.9", "p1 = 7.1  # Größe in µm → ok").encode("utf-8")
        (project / "model.py").write_bytes(modified_code)
        run_dir = run_rair(project, "--comment", "Größe → µm", "model.py")

        assert "Größe in µm → ok" in (run_dir / "git_diff.patch").read_text(encoding="utf-8")
        assert "- Comment: Größe → µm" in (run_dir / "info.md").read_text(encoding="utf-8")
        assert load_run(run_dir)["comment"] == "Größe → µm"

        git(project, "checkout", "--", "model.py")
        git(project, "apply", f"rairarchive/runs/{run_dir.name}/git_diff.patch")
        assert (project / "model.py").read_bytes() == modified_code

    def test_no_patch_without_changes(self, project: Path):
        git(project, "checkout", "--", "model.py")
        run_dir = run_rair(project, "model.py")

        assert not (run_dir / "git_diff.patch").exists()
        assert load_run(run_dir)["git"]["has_diff"] is False
        assert "Uncommitted Changes" not in (run_dir / "info.md").read_text(encoding="utf-8")
