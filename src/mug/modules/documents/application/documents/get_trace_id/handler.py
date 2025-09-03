"""Documents.Application.Document.GetTraceId handler.

Generates a new trace/correlation id using the cross-cutting TraceIdProvider.
"""

from mug.common.application.trace import TraceIdProvider
from .query import GetTraceIdQuery


class GetTraceIdHandler:
    """Returns a fresh trace id for document-related operations."""

    def __init__(self, trace_ids: TraceIdProvider) -> None:
        self._trace_ids = trace_ids

    def handle(self, _: GetTraceIdQuery) -> str:
        return self._trace_ids.new_trace_id()