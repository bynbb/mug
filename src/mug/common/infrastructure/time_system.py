"""Common.Infrastructure: system clock implementation (UTC)."""

from datetime import datetime, timezone

from mug.common.application.time import Clock


class SystemClock(Clock):
    """Production time source using the OS clock in UTC."""

    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def now_iso(self) -> str:
        return self.now().isoformat()