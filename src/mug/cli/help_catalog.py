"""Composition-root command catalog.

This keeps cross-module knowledge (module -> commands) OUT of modules like
System. The composition root owns and injects this data via a port.
"""

from typing import Dict, List, Mapping, Sequence


class StaticCommandCatalog:
    """Simple in-memory implementation of the CommandCatalog port."""

    def __init__(self, mapping: Mapping[str, Sequence[str]] | None = None) -> None:
        # Normalize to {str: List[str]} and copy to avoid external mutation
        self._mapping: Dict[str, List[str]] = {
            str(k): list(v) for k, v in (mapping or {}).items()
        }

    def list_commands(self) -> Dict[str, List[str]]:
        """Return a copy of the module -> commands map."""
        return {k: list(v) for k, v in self._mapping.items()}