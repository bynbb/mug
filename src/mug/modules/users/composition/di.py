"""Users module dependency wiring."""

from mug.common.application import Mediator


def register_handlers(mediator: Mediator) -> None:
    """Hook for registering users handlers."""
    return None
