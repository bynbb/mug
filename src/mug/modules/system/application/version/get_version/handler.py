"""System.Application.Version.GetVersion handler.

Reads the system's semantic version via the SystemInfoReader port.
"""

from mug.modules.system.application.ports.system_info_reader import SystemInfoReader
from .query import GetVersionQuery


class GetVersionHandler:
    """Returns the application's version string."""

    def __init__(self, reader: SystemInfoReader) -> None:
        self._reader = reader

    def handle(self, _: GetVersionQuery) -> str:
        return self._reader.get_system_info().version.value
