"""System.Infrastructure: SystemInfoReader implementation.

Reads version/build/runtime metadata from Python package metadata and environment:

- version: importlib.metadata.version(<package>)  (fallback "0.0.0" if missing/invalid)
- built_at: ISO-8601 timestamp from env BUILD_AT (optional)
- started_at: process start time (UTC)
- commit: env GIT_COMMIT (optional)
- name: env APP_NAME or the package name

This keeps all I/O and environment access in Infrastructure.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as pkg_version
from typing import Optional

from mug.modules.system.application.ports.system_info_reader import SystemInfoReader
from mug.modules.system.domain.system_info.entity import SystemInfo
from mug.modules.system.domain.system_info.version import Version


class PackageSystemInfoReader(SystemInfoReader):
    """Reads system information from package metadata and environment."""

    def __init__(self, package_name: str = "mug") -> None:
        self._package_name = package_name
        self._started_at = datetime.fromtimestamp(time.time(), tz=timezone.utc)

    # ---- Port implementation ------------------------------------------------

    def get_system_info(self) -> SystemInfo:
        ver_str = self._read_version(self._package_name) or "0.0.0"
        version = self._coerce_semver(ver_str) or Version("0.0.0")
        return SystemInfo(
            version=version,
            built_at=self._parse_iso(os.getenv("BUILD_AT")),
            started_at=self._started_at,
            commit=os.getenv("GIT_COMMIT"),
            name=os.getenv("APP_NAME") or self._package_name,
        )

    # ---- Helpers ------------------------------------------------------------

    def _read_version(self, package: str) -> Optional[str]:
        try:
            return pkg_version(package)
        except PackageNotFoundError:
            return None
        except Exception:
            # Defensive: if metadata is corrupted, treat as unknown
            return None

    def _coerce_semver(self, raw: str) -> Optional[Version]:
        try:
            return Version(raw)
        except Exception:
            return None

    def _parse_iso(self, s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            # Accept 'Z' suffix as UTC
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None