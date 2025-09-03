"""Common.Application: handler pipeline utilities.

These decorators/helpers standardize how application handlers execute:
- Logging around handler execution
- Converting bare return values into Result[T]
- Mapping exceptions into Problem envelopes (no stack traces to callers)

They are CA-friendly: depend only on Common.Application and Common.Domain.

Example:
    from mug.common.application.pipeline import pipeline
    from mug.common.application.result import Result, ok
    from mug.common.domain.errors import DomainError

    @pipeline()  # adds logging + exception->Problem mapping + result wrapping
    def handle(query: GetThingQuery) -> Result[str] | str:
        if not authorized:
            raise DomainError(code="NOT_AUTHORIZED", message="...")
        return ok("value")  # or just "value" and it will be wrapped

    r = handle(GetThingQuery(...))
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional, TypeVar, Union, cast

from mug.common.application.result import Err, Ok, Problem, Result, err, ok
from mug.common.domain.errors import DomainError  # will be provided in a later step

T = TypeVar("T")


def ensure_result(value: Union[Result[T], T]) -> Result[T]:
    """Return value as Result, wrapping non-Result values with Ok."""
    if isinstance(value, (Ok, Err)):
        return cast(Result[T], value)
    return ok(cast(T, value))


def default_exception_mapper(ex: Exception) -> Problem:
    """Map exceptions to a Problem envelope with stable codes/messages."""
    if isinstance(ex, DomainError):
        # Domain raised a typed error with a stable code
        return Problem(code=ex.code, message=ex.message, details=ex.details)
    if isinstance(ex, ValueError):
        return Problem(code="VALIDATION_ERROR", message=str(ex))
    if isinstance(ex, KeyError):
        return Problem(code="MISSING_KEY", message=str(ex))
    # Catch-all; avoid leaking internal details
    return Problem(code="UNEXPECTED_ERROR", message=str(ex) or ex.__class__.__name__)


def pipeline(
    *,
    logger: Optional[logging.Logger] = None,
    exception_mapper: Optional[Callable[[Exception], Problem]] = None,
) -> Callable[[Callable[..., Union[Result[T], T]]], Callable[..., Result[T]]]:
    """Decorator: add logging + exception→Problem mapping + Result wrapping.

    Args:
        logger: optional logger; defaults to module/function-based logger.
        exception_mapper: optional custom mapper; defaults to `default_exception_mapper`.

    Returns:
        Wrapped callable that always yields `Result[T]`.
    """

    def decorator(func: Callable[..., Union[Result[T], T]]) -> Callable[..., Result[T]]:
        log = logger or logging.getLogger(f"{func.__module__}.{func.__qualname__}")
        map_ex = exception_mapper or default_exception_mapper

        def wrapper(*args: Any, **kwargs: Any) -> Result[T]:
            log.debug("START %s", func.__name__)
            try:
                result = func(*args, **kwargs)
                wrapped = ensure_result(result)
                if isinstance(wrapped, Ok):
                    log.debug("OK %s", func.__name__)
                else:
                    p = wrapped.problem
                    log.warning("ERR %s [%s] %s", func.__name__, p.code, p.message)
                return wrapped
            except Exception as ex:  # noqa: BLE001
                problem = map_ex(ex)
                log.error("EXC %s [%s] %s", func.__name__, problem.code, problem.message)
                return err(problem.code, problem.message, problem.details)

        # Preserve useful metadata
        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        wrapper.__doc__ = getattr(func, "__doc__", None)
        wrapper.__qualname__ = getattr(func, "__qualname__", wrapper.__name__)
        return wrapper

    return decorator


def with_logging(
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., Union[Result[T], T]]], Callable[..., Union[Result[T], T]]]:
    """Decorator: logging only (no exception mapping, no result wrapping)."""

    def decorator(func: Callable[..., Union[Result[T], T]]):
        log = logger or logging.getLogger(f"{func.__module__}.{func.__qualname__}")

        def wrapper(*args: Any, **kwargs: Any):
            log.debug("START %s", func.__name__)
            out = func(*args, **kwargs)
            log.debug("END %s", func.__name__)
            return out

        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        wrapper.__doc__ = getattr(func, "__doc__", None)
        wrapper.__qualname__ = getattr(func, "__qualname__", wrapper.__name__)
        return wrapper

    return decorator


def map_exceptions(
    exception_mapper: Optional[Callable[[Exception], Problem]] = None,
) -> Callable[[Callable[..., Union[Result[T], T]]], Callable[..., Result[T]]]:
    """Decorator: catch exceptions and convert to Err(Problem)."""

    def decorator(func: Callable[..., Union[Result[T], T]]) -> Callable[..., Result[T]]:
        map_ex = exception_mapper or default_exception_mapper
        log = logging.getLogger(f"{func.__module__}.{func.__qualname__}")

        def wrapper(*args: Any, **kwargs: Any) -> Result[T]:
            try:
                return ensure_result(func(*args, **kwargs))
            except Exception as ex:  # noqa: BLE001
                problem = map_ex(ex)
                log.error("EXC %s [%s] %s", func.__name__, problem.code, problem.message)
                return err(problem.code, problem.message, problem.details)

        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        wrapper.__doc__ = getattr(func, "__doc__", None)
        wrapper.__qualname__ = getattr(func, "__qualname__", wrapper.__name__)
        return wrapper

    return decorator