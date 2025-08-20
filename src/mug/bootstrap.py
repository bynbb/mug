# src/mug/bootstrap.py
from __future__ import annotations

import logging

from .error_handling import install_global_error_handler
from .logging_config import configure_logging


def init_app_logging() -> None:
    configure_logging()
    install_global_error_handler()
    logging.getLogger(__name__).debug("Logging + global error handler initialized")
