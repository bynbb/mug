"""Application bootstrap wiring."""

from mug.common.application import Mediator


def bootstrap() -> Mediator:
    """Create application container with telemetry hooks."""
    mediator = Mediator()
    telemetry = None  # placeholder for telemetry hooks
    _ = telemetry  # prevent unused variable
    return mediator
