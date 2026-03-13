# Rair - Research Archival & Integrity Recorder
Disclaimer: Do not use in production yet. This project is early on. Please test it and provide your feedback.

Rair is a CLI-tool for simple data versioning.

When running experiments, model parameters and model details needs to be tweaked
frequently. Committing minimal changes clutters the git history and makes it hard to track
actual model modifications. This package allows to link modeling results to exact code versions
without the need to commit all changes to git. Therefore it archives code diffs alongside the git commit
reference. It tracks input and intermediate data as well to guarantee full reproducibility for every run.

Using heuristics, Rair can be used in many scenarios without any manual configuration.

## Features

- **Auto-discovery**: Automatically discover input/output files using hash-based change detection for outputs
- **Hash caching**: Cache hash calculations in `.rair_cache/` for fast operation on large data files
- **Git diff tracking**: Track uncommitted changes alongside git commits
- **Archive format**: Human-readable markdown and machine-readable JSON
- **Flexible configuration**: Configure via CLI, or config file `.rair.toml`, or `pyproject.toml`
- **Output capture**: Captures stdout/stderr to a file
- **Deduplication**: Avoids storing duplicate data files by using content hashes
- **Selective tracking**: Use `--no-auto-discover` to require explicit `--input`/`--output`
- **Output hardlinks**: `--output-files-in-run` creates hardlinks for easy access
- **Default command**: Configure a default command to run when no script specified
- **Hierarchical config**: Local configs override project settings

## Installation

```bash
pip install git+https://github.com/DLR-Institute-of-Future-Fuels/rair@main
```

## How to use

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

# Selective tracking - specify exactly which files to track
# Use --no-auto-discover to require explicit --input and --output
rair --no-auto-discover --input "data/*.csv" --output "results/*.json" myscript.py

# Run with default command from config
# (requires default_command setting in .rair.toml)
cd project_with_default_command && rair --all

# Create hardlinks to outputs in run folder for easy access
rair --output-files-in-run myscript.py

# Run interactive setup to configure rair for your project
rair --setup
```

### Configuration

In alternative to CLI parameters, configuration can be provided via a `.rair.toml` file or in `pyproject.toml` under `[tool.rair]`.

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
├── .rair.toml              # Project config (input = ["data/*.csv"])
└── experiments/
    ├── .rair.toml          # Local config (input = ["*.json"]) - overrides project
    └── train.py
```

When running `cd experiments && rair train.py`, it uses `experiments/.rair.toml`.
When running `cd project && rair train.py`, it uses project `.rair.toml`.

### CLI Options

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
--setup                    Run interactive setup dialog
--help                     Show help message
```


## How it works

For each run of an experiment, rair creates a new result directory that contains the data files as well as an info file with the git commit reference and the diff with uncommitted changes if there are any.

A diff of the uncommitted changes can look for example like this:
```diff
diff --git a/my_model.py b/my_model.py
index 3bfb495..97ab218 100644
--- a/my_model.py
+++ b/my_model.py
@@ -1,7 +1,7 @@
-p1 = 5.5
-p2 = 9.5
+p1 = 5.0
+p2 = 9.8
```

The info.md file stored for each run includes:
---
# Data information

- Run time: 2026-01-06 15:45:10
- Git hash: [44ec730d0855ac96f435633649e016c56a60cc7e](https://gitlab.dlr.de/krus_ni/simple_data_versioning/-/tree/44ec730d0855ac96f435633649e016c56a60cc7e)
- Git hash short: `44ec730`
- Branch name: `main`
- Tracking branch URL: `https://gitlab.dlr.de/krus_ni/simple_data_versioning.git`
- No uncommitted changes
---

### Directory Structure

The structure of the created result directory can look like this:
```
rairarchive/runs/
    20260124-001-ee207dee/
        git_diff.patch
        info.md
        run.json
        out.txt
    20260124-002-44ec730/
        info.md
        run.json
        out.txt
```

### Restoring Versions

To restore the version a file was created with, the following commands can be used:
```bash
git checkout 44ec730
git apply rairarchive/20260124-001-ee207dee/git_diff.patch
```
