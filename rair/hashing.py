import hashlib
from pathlib import Path
from .utils import HASH_LENGTH

def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()[:HASH_LENGTH]  # truncated to 160 bit
