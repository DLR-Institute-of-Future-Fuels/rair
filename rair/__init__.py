"""Rair - Simple data versioning."""

from .cli import app
from ._version import __version__  # Run "pip install -e ." to generate _version.py

__all__ = ["app"]
