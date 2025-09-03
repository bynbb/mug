"""Common.Application bootstrap.

Wires application-layer contracts and pipelines into the DI container.
MUST NOT import from Infrastructure or module-specific packages to preserve
Clean Architecture dependency direction.
"""

from typing import Any


def add_common_application(services: Any) -> None:
    """Register application-layer services with the container.

    Keep this limited to application-layer concerns (e.g., pipelines, result
    mappers). Avoid importing concretes from Infrastructure.
    """
    # Intentionally empty for now; add application-wide pipelines here later.
    return None