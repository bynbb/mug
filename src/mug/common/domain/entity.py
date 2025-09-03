"""Common.Domain: Entity base class.

- Provides identity-based equality and hashing (by `id` and concrete type)
- Optional domain event stash with add/pull helpers
- Designed to play nicely with dataclasses in subclasses:
  * Subclasses define their own `id` field (e.g., as a dataclass field)
  * No mandatory `super().__init__()` call required
"""

from __future__ import annotations

from typing import Any, Generic, List, TypeVar, TYPE_CHECKING

TId = TypeVar("TId")


if TYPE_CHECKING:
    # Forward reference only; actual definition will live in common.domain.events
    class DomainEvent:  # pragma: no cover - typing aid only
        pass


class Entity(Generic[TId]):
    """Base for aggregate roots and entities with identity semantics.

    Subclasses are expected to define an `id` attribute (hashable). The base
    implements:
      - __eq__/__hash__ by (type, id)
      - domain event helpers (add_domain_event / pull_domain_events)
    """

    # --- Identity semantics -------------------------------------------------
    @property
    def _identity(self) -> Any:
        try:
            return getattr(self, "id")
        except AttributeError as exc:
            raise AttributeError(
                f"{self.__class__.__name__} must define an 'id' attribute "
                "to use Entity identity semantics."
            ) from exc

    def __eq__(self, other: object) -> bool:
        if other is self:
            return True
        if other is None or not isinstance(other, self.__class__):
            return False
        return self._identity == getattr(other, "id", object())

    def __hash__(self) -> int:
        # Hash by concrete type + id to avoid collisions across types sharing ids
        return hash((self.__class__, self._identity))

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.__class__.__name__}(id={self._identity!r})"

    # --- Domain events (optional) -------------------------------------------
    # Stored lazily to avoid interfering with dataclass-generated __init__
    def _event_list(self) -> List["DomainEvent"]:
        lst = getattr(self, "_Entity__domain_events", None)
        if lst is None:
            lst = []
            setattr(self, "_Entity__domain_events", lst)
        return lst

    def add_domain_event(self, event: "DomainEvent") -> None:
        """Record a domain event to be dispatched by the application layer."""
        self._event_list().append(event)

    def pull_domain_events(self) -> List["DomainEvent"]:
        """Return and clear the recorded domain events."""
        events = list(self._event_list())
        self._event_list().clear()
        return events