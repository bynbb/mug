"""Users module dependency wiring."""

from mug.common.application.mediator import Mediator
from mug.modules.users.application.public import (
    CreateUser,
    GetUser,
    make_create_user_handler,
    make_get_user_handler,
)
from mug.modules.users.infrastructure.public import InMemoryUserRepo


def register_handlers(mediator: Mediator) -> None:
    repo = InMemoryUserRepo()
    mediator.register(CreateUser, make_create_user_handler(repo))
    mediator.register(GetUser, make_get_user_handler(repo))
