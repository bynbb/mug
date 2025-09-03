"""Common.Application: trace/correlation id contract."""

from typing import Protocol


class TraceIdProvider(Protocol):
    """Abstraction for generating correlation/trace identifiers."""

    def new_trace_id(self) -> str:
        """Return a new opaque trace id (e.g., UUID4 as a string)."""