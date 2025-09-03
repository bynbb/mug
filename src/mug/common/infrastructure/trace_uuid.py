"""Common.Infrastructure: UUID-based TraceId provider."""

import uuid

from mug.common.application.trace import TraceIdProvider


class UuidTraceIdProvider(TraceIdProvider):
    """Generates opaque correlation/trace identifiers using UUID4."""

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())