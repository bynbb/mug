class DomainError(Exception):
    """Base domain error."""


class ValidationError(DomainError):
    """Input validation failed."""


class NotFound(DomainError):
    """Requested entity not found."""


class Conflict(DomainError):
    """Entity conflict or duplicate."""
