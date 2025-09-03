"""Documents.Application.Documents.GetTraceId: query DTO."""

from pydantic import BaseModel


class GetTraceIdQuery(BaseModel):
    """Empty query for symmetry with other use cases."""
    pass