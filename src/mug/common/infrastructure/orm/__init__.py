"""Common.Infrastructure.ORM utilities (SQLAlchemy).

This package provides small, reusable ORM helpers:
- new_base(): per-module DeclarativeBase factory with naming conventions
- UTCDateTime, GUID: portable column types

Import convenience:
    from mug.common.infrastructure.orm import new_base, UTCDateTime, GUID
"""

from .factory import new_base
from .types import UTCDateTime, GUID

__all__ = ["new_base", "UTCDateTime", "GUID"]