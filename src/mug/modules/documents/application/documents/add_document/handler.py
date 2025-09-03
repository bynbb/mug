"""Documents.Application.Documents.AddDocument handler.

Computes a deterministic XML file path for a new document (no I/O yet).
This lets us exercise CQRS composition and keep storage concerns separate.
"""

from __future__ import annotations

import re
from pathlib import Path

from mug.common.application.time import Clock
from .command import AddDocumentCommand


class AddDocumentHandler:
    """Return a deterministic XML path for a new document."""

    def __init__(self, clock: Clock, base_dir: str = ".mug-data/documents") -> None:
        self._clock = clock
        self._base = Path(base_dir)

    def _slug(self, s: str) -> str:
        s = (s or "").strip().lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        s = re.sub(r"(^-|-$)", "", s)
        return s or "untitled"

    def _stamp(self) -> str:
        """Produce a filesystem-friendly UTC timestamp from ISO-8601."""
        iso = self._clock.now_iso()  # e.g., 2025-09-04T12:34:56.789012+00:00
        # Keep digits and 'T'; strip separators/timezone symbols.
        return re.sub(r"[^0-9T]", "", iso)
        # Example -> 20250904T1234567890120000

    def handle(self, cmd: AddDocumentCommand) -> str:
        slug = self._slug(cmd.title)
        ts = self._stamp()
        name = f"{slug}--{ts}.xml"
        path = (self._base / name).resolve()
        return str(path)