from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

DEFAULT_FMT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def _parse_level(value: int | str, fallback: int = logging.INFO) -> int:
    """Return a logging level int from an int or level name."""
    if isinstance(value, int):
        return value
    try:
        lv = logging.getLevelName(value.upper())
        if isinstance(lv, int):
            return lv
    except Exception:
        pass
    return fallback


def configure_logging(
    level: int | str | None = None,
    log_file: str | None = None,
    fmt: str | None = None,
) -> None:
    """
    Configure root logger with console (StreamHandler) and a rotating file handler.
    Safe to call multiple times.
    """
    # Level: prefer explicit arg, else env, else INFO
    env_level = os.getenv("LOG_LEVEL", "INFO")
    lvl_input: int | str = level if level is not None else env_level
    lvl_int = _parse_level(lvl_input)

    # Log file: prefer explicit arg, else env, else default path
    env_log_file = os.getenv("LOG_FILE", "logs/app.log")
    log_path: str = log_file if isinstance(log_file, str) else env_log_file

    fmt_str = fmt or os.getenv("LOG_FMT", DEFAULT_FMT)

    root = logging.getLogger()
    root.setLevel(lvl_int)

    formatter = logging.Formatter(fmt_str)

    # Console handler (stdout). Don't block on presence of any StreamHandler,
    # because caplog (pytest) may have already attached a handler. Ensure we
    # add one specifically for sys.stdout if it's missing.
    if not any(
      isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout
      for h in root.handlers
    ):
       sh = logging.StreamHandler(stream=sys.stdout)
       sh.setLevel(lvl_int)
       sh.setFormatter(formatter)
       root.addHandler(sh)

    # Ensure log directory exists
    d = os.path.dirname(log_path)
    if d:
        os.makedirs(d, exist_ok=True)

    # Rotating file handler (5 MB, keep 3 backups)
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        fh = RotatingFileHandler(
            filename=log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        fh.setLevel(lvl_int)
        fh.setFormatter(formatter)
        root.addHandler(fh)

    # Route warnings to logging
    logging.captureWarnings(True)

    # Also mirror ERROR+ to stderr for visibility
    if not any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr
        for h in root.handlers
    ):
        err = logging.StreamHandler(stream=sys.stderr)
        err.setLevel(logging.ERROR)
        err.setFormatter(formatter)
        root.addHandler(err)
