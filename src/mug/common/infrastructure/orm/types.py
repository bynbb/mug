"""Common.Infrastructure.ORM: portable SQLAlchemy column types.

- UTCDateTime: timezone-aware UTC datetime storage
- GUID: 36-char UUID-as-text storage (portable across SQLite, Postgres, etc.)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.types import DateTime, String, TypeDecorator


class UTCDateTime(TypeDecorator):
    """Store timezone-aware datetimes normalized to UTC.

    Works with backends that don't enforce timezone awareness (e.g., SQLite).
    Values are coerced to UTC on bind and returned as UTC-aware on result.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect: Any) -> Optional[datetime]:  # noqa: ANN401
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: Optional[datetime], dialect: Any) -> Optional[datetime]:  # noqa: ANN401
        if value is None:
            return None
        # Some drivers return naive datetimes even when timezone=True (e.g., SQLite)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class GUID(TypeDecorator):
    """Store UUID values as 36-character strings (portable).

    Accepts either `uuid.UUID` or `str` on bind and always returns `str`.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:  # noqa: ANN401
        if value is None:
            return None
        try:
            # Avoid importing uuid at module import time to keep light
            import uuid  # local import
            if isinstance(value, uuid.UUID):
                return str(value)
            s = str(value)
            # Validate shape quickly (raise if invalid)
            uuid.UUID(s)
            return s
        except Exception as ex:  # noqa: BLE001
            raise ValueError(f"Invalid GUID value: {value!r}") from ex

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:  # noqa: ANN401
        if value is None:
            return None
        return str(value)