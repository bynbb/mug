"""Common.Application: time contract."""

from typing import Protocol
from datetime import datetime


class Clock(Protocol):
    """Abstract time source (UTC)."""

    def now(self) -> datetime:
        """Return current UTC time."""

    def now_iso(self) -> str:
        """Return current UTC time as an ISO-8601 string."""