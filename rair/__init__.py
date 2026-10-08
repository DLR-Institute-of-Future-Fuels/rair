"""Rair - Simple data versioning."""

from importlib.metadata import version

from .cli import app

__version__ = version("rair")

__all__ = ["app"]
