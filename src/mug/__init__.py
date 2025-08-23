"""mug package"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__: str = _pkg_version("mug")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__", "get_version"]


def get_version() -> str:
    """Return the current version of mug."""
    return __version__
