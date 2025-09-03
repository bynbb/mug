"""System.Application.Help: command discovery port.

This port abstracts how the System module discovers module -> commands mappings.
The composition root (CLI) provides an implementation (e.g., StaticCommandCatalog)
to avoid cross-module knowledge leaking into System.
"""

from typing import Protocol


class CommandCatalog(Protocol):
    """Abstraction for discovering available commands per module."""

    def list_commands(self) -> dict[str, list[str]]:
        """Return a mapping like: {'documents': ['trace-id', 'add', 'db'], ...}."""