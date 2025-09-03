
from dependency_injector import providers

from mug.cli.container import AppContainer
from mug.modules.system.application.help.ports import CommandCatalog
from .registry import SystemRegistry  # <-- delegate to the canonical registry

def add_system_module(services: AppContainer, *, command_catalog: CommandCatalog) -> None:
    """Register the System module into the root container (IServiceCollection analogue)."""
    system = providers.Container(
        SystemRegistry,
        config=services.config.modules.system,
        command_catalog=providers.Object(command_catalog),
    )
    services.system.override(system)
