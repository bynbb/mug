"""Common.Domain: ValueObject base class.

A Value Object is compared by the values of its attributes, not by identity.
Subclasses SHOULD be defined as `@dataclass(frozen=True)` for immutability,
but this base works for non-dataclass classes as well.

Features:
- Equality and hashing by value (class + components tuple)
- Friendly repr()
- Helper `components()` to introspect the tuple used for comparisons
- Helper `copy_with(**changes)` for dataclass-based VOs (uses dataclasses.replace)

Usage (recommended):
    from dataclasses import dataclass
    from mug.common.domain.value_object import ValueObject

    @dataclass(frozen=True)
    class Money(ValueObject):
        amount: int
        currency: str

    assert Money(10, "USD") == Money(10, "USD")
    s = {Money(10, "USD"), Money(10, "USD")}
    assert len(s) == 1
"""

from __future__ import annotations

from dataclasses import is_dataclass, fields, replace
from typing import Any, Tuple


class ValueObject:
    """Base class for DDD Value Objects with value-based equality and hashing."""

    # ---- Equality / Hash by value ------------------------------------------
    def components(self) -> Tuple[Any, ...]:
        """Return the tuple of values used for equality/hash.

        - If subclass is a dataclass: returns dataclass field values in field order.
        - Otherwise: returns public attributes (non-callable, not starting with '_')
          sorted by attribute name for determinism.
        """
        if is_dataclass(self):
            return tuple(getattr(self, f.name) for f in fields(self))
        # Fallback for non-dataclass VOs
        items = []
        for name, value in self.__dict__.items():
            if name.startswith("_"):
                continue
            if callable(value):
                continue
            items.append((name, value))
        items.sort(key=lambda kv: kv[0])
        return tuple(v for _, v in items)

    def __eq__(self, other: object) -> bool:
        if other is self:
            return True
        if other is None or other.__class__ is not self.__class__:
            return False
        return self.components() == getattr(other, "components")()

    def __hash__(self) -> int:
        return hash((self.__class__, self.components()))

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        if is_dataclass(self):
            parts = ", ".join(f"{f.name}={getattr(self, f.name)!r}" for f in fields(self))
        else:
            comps = self.components()
            parts = ", ".join(repr(c) for c in comps)
        return f"{self.__class__.__name__}({parts})"

    # ---- Utilities ----------------------------------------------------------
    def copy_with(self, **changes: Any):
        """Return a copy with `changes` applied (dataclasses only).

        Raises:
            TypeError: if the subclass is not a dataclass.
        """
        if not is_dataclass(self):
            raise TypeError(f"{self.__class__.__name__}.copy_with requires a dataclass-based ValueObject")
        return replace(self, **changes)