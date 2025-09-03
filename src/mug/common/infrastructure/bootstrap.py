"""Common.Infrastructure bootstrap.

Binds infrastructure concretes to abstract providers declared in the root DI
container. Keep this module free of any module-specific imports.

- Clock -> SystemClock
- LoggingInitializer -> LoggingInitializer(level)
"""

from dependency_injector import providers

from mug.common.infrastructure.time_system import SystemClock
from mug.common.infrastructure.logging_init import LoggingInitializer


def add_common_infrastructure(services, *, log_level: str = "INFO") -> None:
    """Register infrastructure implementations into the DI container."""
    # Time source (UTC)
    services.clock.override(providers.Factory(SystemClock))

    # Logging initializer (one-time setup at composition root)
    services.logging_initializer.override(
        providers.Factory(LoggingInitializer, level=log_level)
    )