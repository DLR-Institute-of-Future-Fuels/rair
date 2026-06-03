"""End-to-end tests for the CLI application."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rair.cli import app


OUTPUT_DIR = Path(__file__).parent / "output"


def setup_git_repo(project_dir: Path) -> None:
    """Initialize a git repository in the project directory."""
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=project_dir, check=True, capture_output=True)


@pytest.fixture(scope="module")
def temp_project_dir():
    """Create a temp project directory with git and mymodel.py copied in."""
    tmpdir = tempfile.mkdtemp()
    project_dir = Path(tmpdir) / "project"
    project_dir.mkdir()

    source_script = Path(__file__).parent / "mymodel.py"
    dest_script = project_dir / "mymodel.py"
    shutil.copy(source_script, dest_script)

    setup_git_repo(project_dir)

    # Simulate a code change by modifying the script before running tests
    content = dest_script.read_text()
    content = content.replace("p1 = 5.9", "p1 = 7.1")
    content = content.replace("p2 = 9.5", "p2 = 3.3")
    dest_script.write_text(content)

    yield project_dir

    try:
        shutil.rmtree(tmpdir)
    except PermissionError:
        import os
        import stat
        def onerror(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(tmpdir, onerror=onerror)


@pytest.fixture(scope="module", autouse=True)
def copy_output_after_tests(temp_project_dir: Path):
    """Copy archive to tests/output after all tests in this module pass."""
    yield
    archive_dir = temp_project_dir / "rairarchive"
    if archive_dir.exists():
        OUTPUT_DIR.mkdir(exist_ok=True)
        output_archive = OUTPUT_DIR / "rairarchive"
        if output_archive.exists():
            shutil.rmtree(output_archive)
        shutil.copytree(archive_dir, output_archive)


class TestCLIE2E:
    """End-to-end integration tests using the Typer CLI runner."""

    def test_e2e_with_mymodel_script(self, temp_project_dir: Path):
        """Run mymodel.py end-to-end in a temp directory with git."""
        runner = CliRunner()
        dest_script = "mymodel.py"

        import os
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        try:
            result = runner.invoke(app, [str(dest_script)])
        finally:
            os.chdir(original_cwd)
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        archive_dir = temp_project_dir / "rairarchive"
        assert archive_dir.exists(), f"Archive directory not created: {archive_dir}"
        assert (archive_dir / "runs").exists(), "Archive runs directory not created"
        run_dirs = [d for d in (archive_dir / "runs").iterdir() if d.is_dir()]
        assert len(run_dirs) > 0, "No run directories created"
        assert (run_dirs[0] / "run.json").exists(), "run.json not created"

        assert (temp_project_dir / "test_result.txt").exists(), "test_result.txt not in project dir"

    def test_e2e_with_mymodel_script_and_args(self, temp_project_dir: Path):
        """Run mymodel.py end-to-end with script arguments."""
        runner = CliRunner()
        dest_script = "mymodel.py"

        import os
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        try:
            result = runner.invoke(app, [str(dest_script), "--", "extra_arg"])
        finally:
            os.chdir(original_cwd)
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        archive_dir = temp_project_dir / "rairarchive"
        assert archive_dir.exists(), f"Archive directory not created: {archive_dir}"
        assert (archive_dir / "runs").exists(), "Archive runs directory not created"
        run_dirs = [d for d in (archive_dir / "runs").iterdir() if d.is_dir()]
        assert len(run_dirs) > 0, "No run directories created"
        assert (run_dirs[0] / "run.json").exists(), "run.json not created"

        assert (temp_project_dir / "test_result.txt").exists(), "test_result.txt not in project dir"