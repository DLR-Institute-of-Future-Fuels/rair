# Simple Data Versioning

This is an experimental Python package for simple data versioning.

When running experiments, model parameters and model details needs to be tweaked
frequently. Committing minimal changes clutters the git history and makes it hard to track
actual model modifications. This package allows to link data files to exact code versions
without the need to commit all changes to git. It stores code diffs alongside the git commit
reference.

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

For each run of an experiment, a new result directory is created that contains
the data files as well as an info file with the git commit reference and
the diff with uncommitted changes if there are any.:

---
# Data information

- Run time: 2026-01-06 15:45:10
- Git hash: [44ec730d0855ac96f435633649e016c56a60cc7e](https://gitlab.dlr.de/krus_ni/simple_data_versioning/-/tree/44ec730d0855ac96f435633649e016c56a60cc7e)
- Git hash short: `44ec730`
- Branch name: `main`
- Tracking branch URL: `https://gitlab.dlr.de/krus_ni/simple_data_versioning.git`
- No uncommitted changes
---

## How to use

```python
import test_data_versioning

p1 = 5.0
p2 = 9.8

# Create a new result directory in the format
# my_results/YYYYMMDD-HHMMSS_<git-hash>[_<diff-hash>]/
# and get a prefix for saving result files
file_prefix = test_data_versioning.get_result_prefix("my_results")

# Save the modeling results to the created directory
with open(f"{file_prefix}data.txt", "w") as f:
    f.write(f"Result: {p1 * p2}\n")

```

The structure of the created result directory can look like this:
```
my_results/
    20260106-154510_44ec730-1a2b3c/
        data.txt
        git_diff.patch
        info.md
    20260107-101530_44ec730/
        data.txt
        info.md
    20260107-101635_44ec730-4d5e6f/
        data.txt
        git_diff.patch
        info.md
```