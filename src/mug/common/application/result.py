"""Common.Application: Result/Problem primitives.

Lightweight functional-style result envelope inspired by .NET's Result<T>.
Handlers can return `Result[T]` instead of raising, and Presentation can render
success/failure uniformly.

Usage:
    from mug.common.application.result import Result, ok, err, is_ok, unwrap_or

    def handle(...) -> Result[str]:
        if bad:
            return err("DOC_NOT_UNIQUE", "Document title must be unique", {"title": t})
        return ok("done")

    r = handle(...)
    if is_ok(r):
        print(r.value)
    else:
        print(r.problem.code, r.problem.message)
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Problem:
    """Standard error envelope for application/domain failures."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class Ok(Generic[T]):
    """Successful result."""
    value: T


@dataclass(frozen=True)
class Err:
    """Failed result."""
    problem: Problem


# Public result type alias
Result = Union[Ok[T], Err]


# --------- Constructors ---------
def ok(value: T) -> Ok[T]:
    """Create a successful Result."""
    return Ok(value)


def err(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Err:
    """Create a failed Result with a Problem envelope."""
    return Err(Problem(code=code, message=message, details=details))


# --------- Introspection helpers ---------
def is_ok(result: Result) -> bool:
    return isinstance(result, Ok)


def is_err(result: Result) -> bool:
    return isinstance(result, Err)


# --------- Unwrap helpers (safe defaults) ---------
def unwrap(result: Result[T]) -> T:
    """Return value or raise RuntimeError with Problem info."""
    if isinstance(result, Ok):
        return result.value
    p = result.problem  # type: ignore[attr-defined]
    raise RuntimeError(f"{p.code}: {p.message}")


def unwrap_or(result: Result[T], default: T) -> T:
    """Return value or a provided default."""
    return result.value if isinstance(result, Ok) else default


# --------- Functional helpers ---------
def map_value(result: Result[T], fn: Callable[[T], U]) -> Result[U]:
    """Transform the success value; propagate error unchanged."""
    if isinstance(result, Ok):
        try:
            return ok(fn(result.value))
        except Exception as ex:  # last-resort guard; don't crash pipeline
            return err("UNEXPECTED_MAP_ERROR", str(ex))
    return result  # type: ignore[return-value]


def bind(result: Result[T], fn: Callable[[T], Result[U]]) -> Result[U]:
    """Monadic bind: if ok, call fn(value) -> Result[U]; else propagate Err."""
    if isinstance(result, Ok):
        try:
            return fn(result.value)
        except Exception as ex:
            return err("UNEXPECTED_BIND_ERROR", str(ex))
    return result  # type: ignore[return-value]


def map_problem(result: Result[T], fn: Callable[[Problem], Problem]) -> Result[T]:
    """Transform the Problem of an Err; pass Ok through."""
    if isinstance(result, Err):
        try:
            return Err(fn(result.problem))
        except Exception as ex:
            return Err(Problem(code="UNEXPECTED_PROBLEM_MAP_ERROR", message=str(ex)))
    return result