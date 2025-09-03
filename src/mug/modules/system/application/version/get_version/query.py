"""System.Application.Version.GetVersion: query DTO."""

from pydantic import BaseModel


class GetVersionQuery(BaseModel):
    """Empty query DTO for symmetry with other use cases."""
    pass
