# Rair - Simple Data Versioning for Python Experiments

This is an Python package for data versioning.

When running experiments, model parameters and model details needs to be tweaked
frequently. Committing minimal changes clutters the git history and makes it hard to track
actual model modifications. This package allows to link data files to exact code versions
without the need to commit all changes to git. It stores code diffs alongside the git commit
reference.

## Installation

```bash
pip install rair
```

## How to use

```bash
# Run a Python script
rair myscript.py arg1 arg2

# Run with explicit command
rair python mymodel.py arg1 arg2

# The first argument can be a Python script or any arbitrary command
rair make --all

# It can be manually specified which files to track
rair --input "data/*.csv" --output "results/*.json" myscript.py

# If only input files are specified, outputs are auto-discovered
rair --input "data/*.csv" --input parameters.txt myscript.py 
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
```

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
--help                     Show help message
```

### Features

- **Auto-discovery**: Automatically discover input/output files using hash-based change detection
- **Hash caching**: Cache file hashes in `.rair_cache/` directory for faster subsequent runs
- **Git diff tracking**: Track uncommitted changes alongside git commits

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

The info file stored with each result includes:
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
git apply rairarchive/20260106-154510_44ec730-1a2b3c/git_diff.patch
```