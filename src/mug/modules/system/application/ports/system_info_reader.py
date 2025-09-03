"""System.Application.Ports: SystemInfoReader port.

Abstraction for reading system metadata (version, build/run info).
Implemented in Infrastructure (e.g., reading from package metadata/env).
"""

from typing import Protocol

from mug.modules.system.domain.system_info.entity import SystemInfo


class SystemInfoReader(Protocol):
    """Port that supplies a snapshot of system information."""

    def get_system_info(self) -> SystemInfo:
        """Return the current SystemInfo snapshot."""