"""Common.Presentation: OutputPort protocol and helpers.

Clean Architecture presenter abstraction:
- Application use cases produce `Result[T]`.
- Presentation implements an `OutputPort[T]` to render either the value or a Problem.
- Use the `present(port, result)` helper to route success/error uniformly.

This module defines only the protocol and tiny helpers.
Concrete presenters (e.g., CLI text/JSON) live in `common/presentation/cli_presenters.py`.
"""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from mug.common.application.result import Err, Ok, Problem, Result

T = TypeVar("T")


class OutputPort(Protocol, Generic[T]):
    """Presenter contract for rendering a use case result."""

    def present_ok(self, value: T) -> None:
        """Render a successful outcome."""

    def present_err(self, problem: Problem) -> None:
        """Render a failure with a structured problem."""


def present(port: OutputPort[T], result: Result[T]) -> None:
    """Dispatch a `Result[T]` to the appropriate OutputPort method."""
    if isinstance(result, Ok):
        port.present_ok(result.value)
    elif isinstance(result, Err):
        port.present_err(result.problem)
    else:  # pragma: no cover - defensive guard
        # Should never happen if handlers return Result[T]
        port.present_err(Problem(code="UNEXPECTED_RESULT_TYPE", message=str(type(result))))