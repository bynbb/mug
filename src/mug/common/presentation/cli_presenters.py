"""Common.Presentation: CLI presenters for Result/Problem.

Two concrete OutputPorts for CLI scenarios:

- TextPresenter[T]: writes human-friendly lines (default to `print`)
- JsonPresenter[T]: writes structured JSON (default to `print(json)`)

You can pass a custom `write` callable (e.g., `typer.echo`) and optional value
formatters. These presenters never raise; they degrade gracefully to string
representations when values aren't JSON-serializable.

Example:
    from mug.common.presentation.cli_presenters import TextPresenter, JsonPresenter
    from mug.common.presentation.output import present
    from mug.common.application.result import ok, err

    tp = TextPresenter[str](write=typer.echo)
    present(tp, ok("done"))   # prints: done

    jp = JsonPresenter[str](write=typer.echo)
    present(jp, err("NOT_FOUND", "Missing thing", {"id": 1}))
    # prints: {"ok": false, "error": {"code": "NOT_FOUND", "message": "Missing thing", "details": {"id": 1}}}
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Generic, Optional, TypeVar

from mug.common.application.result import Problem
from mug.common.presentation.output import OutputPort

T = TypeVar("T")

# ---------- generic JSON fallback -------------------------------------------


def _json_default(o: Any) -> Any:
    """Best-effort JSON serializer for common Python types."""
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Path):
        return str(o)
    if is_dataclass(o):
        return asdict(o)
    if hasattr(o, "__dict__"):
        # last resort: object's dict (non-callables, public attrs)
        return {k: v for k, v in vars(o).items() if not callable(v) and not k.startswith("_")}
    return repr(o)


# ---------- Text presenter ---------------------------------------------------


class TextPresenter(OutputPort[T], Generic[T]):
    """Human-friendly CLI presenter (plain text lines)."""

    def __init__(
        self,
        *,
        write: Optional[Callable[[str], None]] = None,
        value_fmt: Optional[Callable[[T], str]] = None,
        problem_prefix: str = "ERROR: ",
        problem_details_json: bool = True,
    ) -> None:
        self._write = write or (lambda s: print(s, flush=True))
        self._value_fmt = value_fmt or (lambda v: str(v))
        self._problem_prefix = problem_prefix
        self._problem_details_json = problem_details_json

    def present_ok(self, value: T) -> None:
        try:
            self._write(self._value_fmt(value))
        except Exception as ex:  # noqa: BLE001
            self._write(f"{self._value_fmt.__name__ if hasattr(self._value_fmt,'__name__') else 'value'}: {value!r} (format error: {ex})")

    def present_err(self, problem: Problem) -> None:
        base = f"{self._problem_prefix}[{problem.code}] {problem.message}"
        if problem.details:
            try:
                if self._problem_details_json:
                    details = json.dumps(problem.details, default=_json_default, ensure_ascii=False)
                else:
                    details = str(problem.details)
                base = f"{base} | details={details}"
            except Exception:  # best-effort
                base = f"{base} | details=<unprintable>"
        self._write(base)


# ---------- JSON presenter ---------------------------------------------------


class JsonPresenter(OutputPort[T], Generic[T]):
    """Structured JSON presenter for automated consumption."""

    def __init__(
        self,
        *,
        write: Optional[Callable[[str], None]] = None,
        default: Optional[Callable[[Any], Any]] = None,
        indent: Optional[int] = None,
    ) -> None:
        self._write = write or (lambda s: print(s, flush=True))
        self._default = default or _json_default
        self._indent = indent

    def present_ok(self, value: T) -> None:
        payload = {"ok": True, "value": value}
        try:
            self._write(json.dumps(payload, default=self._default, ensure_ascii=False, indent=self._indent))
        except Exception:  # noqa: BLE001
            # Fallback to repr if value is completely non-serializable
            self._write(json.dumps({"ok": True, "value": repr(value)}, ensure_ascii=False, indent=self._indent))

    def present_err(self, problem: Problem) -> None:
        payload = {"ok": False, "error": asdict(problem)}
        try:
            self._write(json.dumps(payload, default=self._default, ensure_ascii=False, indent=self._indent))
        except Exception:  # noqa: BLE001
            # Fallback to minimal structure
            self._write(
                json.dumps(
                    {"ok": False, "error": {"code": problem.code, "message": problem.message}},
                    ensure_ascii=False,
                    indent=self._indent,
                )
            )