"""Common.Domain: domain error types.

A lightweight base exception for domain-level failures with a stable error code.
Domain model and application services can raise `DomainError(code=..., message=...)`
instead of generic exceptions. The application pipeline can then translate these
into a uniform Problem/Result for Presentation.

Usage:
    from mug.common.domain.errors import DomainError, NotFoundError

    if not doc:
        raise NotFoundError(code="DOC_NOT_FOUND", message="Document does not exist", details={"id": doc_id})
    if not is_valid(title):
        raise DomainError(code="DOC_TITLE_INVALID", message="Title is invalid")

Notes:
- Keep messages user-friendly; internal details should go in `details`.
- Error codes should be stable and machine-readable (UPPER_SNAKE_CASE).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base domain exception with a stable error code and optional details."""

    def __init__(self, *, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.code}: {self.message}"

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"DomainError(code={self.code!r}, message={self.message!r}, details={self.details!r})"


class ValidationError(DomainError):
    """Validation failure in domain rules."""


class NotFoundError(DomainError):
    """Entity/aggregate not found."""


class ConflictError(DomainError):
    """State conflict (e.g., uniqueness, concurrency)."""