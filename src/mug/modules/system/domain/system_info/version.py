"""System.Domain.SystemInfo: semantic Version value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mug.common.domain.value_object import ValueObject


# Basic SemVer: MAJOR.MINOR.PATCH with optional -prerelease and +build
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass(frozen=True)
class Version(ValueObject):
    """Immutable semantic version.

    Examples:
        1.0.0
        2.1.3-alpha.1
        0.9.0+build.5
        3.2.1-rc.2+20240904
    """
    value: str

    def __post_init__(self) -> None:
        if not _SEMVER_RE.match(self.value or ""):
            raise ValueError(f"Invalid semantic version: {self.value!r}")

    # Convenience accessors ---------------------------------------------------
    @property
    def major(self) -> int:
        return int(_SEMVER_RE.match(self.value).group(1))  # type: ignore[union-attr]

    @property
    def minor(self) -> int:
        return int(_SEMVER_RE.match(self.value).group(2))  # type: ignore[union-attr]

    @property
    def patch(self) -> int:
        return int(_SEMVER_RE.match(self.value).group(3))  # type: ignore[union-attr]

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.value