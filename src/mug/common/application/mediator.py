from __future__ import annotations

import inspect
from typing import Any, Callable, MutableMapping, Type

Handler = Callable[[Any], Any]
Send = Callable[[Any], Any]


class Mediator:
    """Simple message mediator.

    Handlers are matched on the *exact* type of the message instance.
    """

    def __init__(self) -> None:
        self._handlers: MutableMapping[Type[Any], Handler] = {}

    def register(self, message_type: Type[Any], handler: Handler) -> None:
        """Register a handler for ``message_type``.

        Raises ``ValueError`` if a handler is already registered for the type.
        """
        if message_type in self._handlers:
            raise ValueError(f"Handler for {message_type.__name__} already registered")
        self._handlers[message_type] = handler

    async def send(self, message: Any) -> Any:
        """Dispatch ``message`` to its handler.

        The handler's return value is awaited when it is awaitable.
        """
        handler = self._handlers.get(type(message))
        if handler is None:
            raise KeyError(f"No handler for {type(message).__name__}")
        result = handler(message)
        if inspect.isawaitable(result):
            return await result
        return result
