"""Common.Infrastructure: logging initializer.

Sets up application-wide logging with a consistent format and level.
Intended to be invoked once from the composition root.
"""

import logging
from typing import Optional


_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


class LoggingInitializer:
    """Idempotent logging bootstrapper."""

    def __init__(self, level: str = "INFO", fmt: Optional[str] = None) -> None:
        self._level_name = level
        self._fmt = fmt or "%(asctime)s %(levelname)s [%(name)s] %(message)s"

    def initialize(self) -> None:
        """Initialize root logger.

        If handlers already exist (e.g., tests or a parent framework configured
        logging), just adjust levels; otherwise call basicConfig().
        """
        level = _LEVELS.get(self._level_name.upper(), logging.INFO)
        root = logging.getLogger()

        if root.handlers:
            root.setLevel(level)
            for h in root.handlers:
                try:
                    h.setLevel(level)
                except Exception:  # pragma: no cover - defensive
                    pass
        else:
            logging.basicConfig(level=level, format=self._fmt)