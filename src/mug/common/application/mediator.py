import inspect
from typing import Any, Callable, Dict, Type

Handler = Callable[[Any], Any]


class Mediator:
    """Simple message mediator."""

    def __init__(self) -> None:
        self._handlers: Dict[Type[Any], Handler] = {}

    def register(self, message_type: Type[Any], handler: Handler) -> None:
        if message_type in self._handlers:
            raise ValueError(f"Handler already registered for {message_type.__name__}")
        self._handlers[message_type] = handler

    async def send(self, message: Any) -> Any:
        handler = self._handlers.get(type(message))
        if not handler:
            raise KeyError(f"No handler for {type(message).__name__}")
        result = handler(message)
        return await result if inspect.isawaitable(result) else result


Send = Callable[[Any], Any]
