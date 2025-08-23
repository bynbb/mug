from typing import Type

from mug.common.application.mediator import Mediator
from mug.common.domain.errors import Conflict, DomainError, NotFound, ValidationError
from .telemetry import Telemetry


class AppContainer:
    def __init__(self) -> None:
        self.mediator = Mediator()
        self.telemetry = Telemetry()
        # settings, etc. can be attached later


def bootstrap() -> AppContainer:
    c = AppContainer()
    # --- handler registration happens here (see step 4) ---
    from mug.modules.users.composition.di import register_handlers

    register_handlers(c.mediator)
    return c


EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_NOT_FOUND = 3
EXIT_CONFLICT = 4
EXIT_UNKNOWN = 1


def exit_code_for(exc_type: Type[BaseException]) -> int:
    if issubclass(exc_type, ValidationError):
        return EXIT_VALIDATION
    if issubclass(exc_type, NotFound):
        return EXIT_NOT_FOUND
    if issubclass(exc_type, Conflict):
        return EXIT_CONFLICT
    if issubclass(exc_type, DomainError):
        return EXIT_UNKNOWN
    return EXIT_UNKNOWN
