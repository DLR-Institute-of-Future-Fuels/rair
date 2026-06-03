# Rair - Research Archival & Integrity Recorder
Rair is a CLI-tool for simple data versioning.

When running experiments, model parameters and model details needs to be tweaked
frequently. Committing minimal changes clutters the git history and makes it hard to track
actual program modifications. Rair allows to link computation results to exact code versions
without the need to commit all changes to git. Therefore it stores code diffs alongside the git commit
reference. It tracks input and intermediate data as well to guarantee full reproducibility for every run.

Using heuristics, Rair can be used in many scenarios without any manual configuration.

## Usage example
Suppose you have a simple script `mymodel.py` committed to git, looking like this:

```python
import time

print('Test text output to stdio')
p1 = 5.9
p2 = 9.5

with open("test_result.txt", "w") as f:
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"Current time: {current_time}\n")
    f.write(f"result = {p1 + p2}\n")
```

You tune some parameters (here `p1` and `p2`) without committing the changes to git.

Now you run your script like this:

```bash
rair mymodel.py
```

Rair runs the script and creates an archive with the following structure:

```
rairarchive/
├── data/
│   └── 9157ce88256e95668977_test_result.txt  # deduplicated data file
└── runs/
    └── 20260603-001-023aa51f/
        ├── info.md          # human-readable run overview
        ├── run.json         # machine-readable run metadata
        ├── out.txt          # captured stdout/stderr
        ├── git_diff.patch   # uncommitted changes (patch format)
        └── test_result.txt  # output file (hardlink)
```

The file `info.md` gives an overview of the run:

```markdown
# Run Information
- Start time: 2026-06-03 11:53:09
- Execution time: 0.185 s
- Command: `python mymodel.py`
- Run hash: `023aa51fa4981ebe097f2045947d2108cff014c42332d5f6ef5a9d71cbf5273b`

## Git Information
- Commit: `95aa8c491f8a3e5c44890ea3c6616e123692c4cd`
- Short git hash: `95aa8c4`
- Branch: `main`
- Tracking URL: `no-upstream`

## Uncommitted Changes
in mymodel.py:
p1 = 7.1
p2 = 3.3

## Output Files
- `test_result.txt` -> `rairarchive/data/9157ce88256e95668977_test_result.txt` (hash: `9157ce88`)
```

The "Run hash" captures the git hash, code diff, command line parameters and input file content.

## Install
Rair can be installed with pip. Its tested on Windows and Unix:

```bash
pip install rair
```

## Features
- **Git diff tracking**: Track uncommitted changes alongside git commits
- **Output capture**: Captures stdout/stderr to a file
- **Metadata format**: Human-readable markdown and machine-readable JSON
- **Auto-discovery**: Automatically discover input/output files using hash-based change detection for outputs
- **Deduplication**: Avoids storing duplicate data files by using file hashes
- **Flexible configuration**: Configure via CLI, or config file `.rair.toml`, or `pyproject.toml`

## Running Rair
```bash
# Run a Python script with automatic tracking of all data files
# in the project directory
rair myscript.py

# Run a Python script with script arguments
rair myscript.py arg1 arg2

# Run with explicit command
rair python3 mymodel.py arg1 arg2

# The first argument can be a Python script or any arbitrary command
rair make --all

# Manually specify which files to track
rair --input "data/*.csv" --output "results/*.json" myscript.py

# If only input files are specified, outputs are auto-discovered
rair --input "data/*.csv" --input parameters.txt myscript.py

# Auto-discovery of files can be disabled
rair --no-auto-discover --output "results/*.json" myscript.py

# Run the default command specified in the config file and add
# a comment that is stored with the results
rair --comment "experiment 1"
```

### Automatic data file tracking
By default Rair will track all files in the project directory that are not tracked by git as input data files. Output files are discovered by comparing file hashes before and after the run. This allows to track all relevant files without the need to specify them manually. File hashes are cached in `.rair_cache/` and are recalculated for files with a changed modification time.

### All CLI flags
```
--config FILE              Path to config file
--input TEXT               Glob pattern for input files to track
--output TEXT              Glob pattern for output files to track
--exclude TEXT             Glob pattern to exclude from tracking
--archive-dir DIRECTORY    Directory for archive data (default: rairarchive)
--autodata DIRECTORY       Directory for auto-discovering input/output files
--capture-output/--no-capture-output
                            Capture stdout to out.txt [default: enabled]
--auto-discover/--no-auto-discover
                            Enable/disable auto-discovery [default: enabled]
--output-files-in-run      Create hardlinks to output files in run folder
--comment TEXT             Add a comment to the run
--setup                    Run interactive setup dialog
--help                     Show help message
```

## Configuration
As alternative to CLI parameters, configuration can be provided via a `.rair.toml` file or in `pyproject.toml` under `[tool.rair]`:

**.rair.toml:**
```toml
archive_dir = "rairarchive"
input_glob = ["data/*.csv", "cache/*.pkl"]
output_glob = ["results/*.json", "logs/*.txt"]
exclude_glob = ["data/temp/*"]
autodata_dir = "./data"
capture_output = true
auto_discover = true          # Enable auto-discovery (default)
output_files_in_run = false   # Create hardlinks to outputs in run folder
default_command = "make"      # Default command when no script specified
```

**pyproject.toml:**
```toml
[tool.rair]
archive_dir = "rairarchive"
input = ["data/*.csv", "cache/*.pkl"]
output = ["results/*.json", "logs/*.txt"]
exclude = ["data/temp/*"]
autodata_dir = "./data"
capture_output = true
auto_discover = true          # Enable auto-discovery
output_files_in_run = false   # Create hardlinks to outputs in run folder
default_command = "make"      # Default command when no script specified
```

### Hierarchical Configuration
You can have different configurations for different directories:

- A `.rair.toml` in the current directory overrides project-level config
- Use `rair --setup` in subdirectories to create local configs
- Run `rair --setup` and choose "(c)urrent directory" or "(p)roject"

Example directory structure:
```
project/
├── .rair.toml          # Project config
└── experiments/
    ├── .rair.toml      # Pverrides project config
    └── train.py
```

## Developer Guide
Feedback and contributions are welcome - please open an issue or submit a pull request on GitHub.

To get started with development, first clone the repository:

```bash
git clone https://github.com/DLR-Institute-of-Future-Fuels/rair.git
cd rair
```

You may set up a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: `.venv\Scripts\activate`
```

Build and install the package and dev dependencies:

```bash
pip install -e .[dev]
```

Run the tests:

```bash
pytest
```

## License
This project is licensed under the MIT license - see the [LICENSE](LICENSE) file for details.