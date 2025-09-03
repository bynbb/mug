"""System.Domain.SystemInfo: immutable snapshot of system metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .version import Version


@dataclass(frozen=True)
class SystemInfo:
    """Immutable system information aggregate.

    Captures the running application's identity and build/runtime metadata.
    This is a pure domain structure—no I/O, no infrastructure concerns.

    Attributes:
        version: semantic version of the running application.
        built_at: build timestamp (UTC) if available.
        started_at: process start timestamp (UTC) if available.
        commit: source control commit hash, if embedded.
        name: logical application name (e.g., package name).
    """

    version: Version
    built_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    commit: Optional[str] = None
    name: Optional[str] = None