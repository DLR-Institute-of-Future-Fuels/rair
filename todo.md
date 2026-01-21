# Project
New name of the python package: Rair

Step todo:
- use python environment .venv
- use type annotations, check with mypy
- read README.md and the draft test_data_versioning.py
- restructure code as standard for modern python package
- Rewrite that no extra python code is required in the project where its used
    - instead of python my_model.py it should be used like this: rair my_model.py
    - it should be possible to use it without importing rair in my_model.py
    - input data and result data should be tracked
        - by specifying input and result file/dirs (glob)
        - exclude file/dirs (glob)
        - default to auto-track all files that are
            - not tracked by git
            - not staring with a . or being in a directory starting with a .
            - not hidden
        - rair command should check the tracked files before and after running the python script (my_model.py in the example)
        - since data files might be large, tracking should be efficient
            - use file hashes over the whole file
            - i think checking date/time of last change should be added to prevent calculating the hash every time
            - use a folder .rair_cache for caching this info
        - copy the data in a data archive folder
            - default name "rairarchive/data", but should be configurable
            - store a unique file only a single time - maybe with its hash as name
            - reference them with the annotation of the original file name in the rairarchive/runs/<DATE>-<TIME>_<HASH1>_<HASH2>/info.md generated for each run

- write unit tests for components, get sure they can be tested well in isolation and rund them with pytest
