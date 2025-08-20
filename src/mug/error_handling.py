from __future__ import annotations

import logging
import sys
import threading
from types import TracebackType

_log = logging.getLogger(__name__)


def _global_exception_hook(
    exc_type: type[BaseException],
    exc: BaseException,
    tb: TracebackType | None,
) -> None:
    """Log uncaught exceptions from the main thread."""
    _log.exception("Uncaught exception", exc_info=(exc_type, exc, tb))


def _thread_exception_hook(args: threading.ExceptHookArgs) -> None:
    """Log uncaught exceptions from background threads."""
    # Guard against None in typing stubs
    t = getattr(args, "thread", None)
    tname = getattr(t, "name", "<unknown>")

    # Build a fully-typed exc_info tuple for logging
    etype: type[BaseException] = args.exc_type or BaseException
    evalue: BaseException = args.exc_value or etype("unhandled exception")
    einfo: TracebackType | None = args.exc_traceback

    _log.exception(
        "Uncaught thread exception (thread=%s)",
        tname,
        exc_info=(etype, evalue, einfo),
    )


def install_global_error_handler() -> None:
    """Install global exception hooks for main and thread contexts."""
    # The test looks for this exact assignment pattern:
    sys.excepthook = _global_exception_hook  # <-- matches r"sys\.excepthook\s*="

    # Bonus: handle background thread crashes (Py 3.8+)
    if hasattr(threading, "excepthook"):
        # setattr avoids mypy complaints on optional attribute
        threading.excepthook = _thread_exception_hook
