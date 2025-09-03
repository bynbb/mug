"""Common.Domain: domain event base type.

Immutable base class for domain events:
- UTC timestamp (`occurred_on`) set at creation
- Optional `correlation_id` for tracing across layers/transactions
- `event_name` convenience property (defaults to the concrete class name)

Subclasses add their own specific, immutable fields:

    from dataclasses import dataclass
    from mug.common.domain.events import DomainEvent

    @dataclass(frozen=True)
    class DocumentAdded(DomainEvent):
        document_id: str
        title: str
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class DomainEvent:
    """Base immutable event raised by the Domain."""
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None

    @property
    def event_name(self) -> str:
        """A stable, human-readable name (defaults to the concrete class name)."""
        return self.__class__.__name__