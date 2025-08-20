"""
mug package

CLI to capture, tag, and query project documents with user-defined XML/tags.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    # Distribution name is the project name in pyproject.toml
    __version__: str = _pkg_version("mug")
except PackageNotFoundError:
    # When running from a source tree without an installed distribution.
    __version__ = "0.0.0"

__all__ = ["__version__", "get_version"]

def get_version() -> str:
    """Return the current version of mug."""
    return __version__
