# src/mug/modules/system/infrastructure/registry.py
from dependency_injector import containers, providers

from mug.modules.system.infrastructure.system_info_reader import PackageSystemInfoReader
from mug.modules.system.application.version.get_version.handler import GetVersionHandler
from mug.modules.system.application.help.get_help.handler import GetHelpHandler
from mug.modules.system.application.help.ports import CommandCatalog

class SystemRegistry(containers.DeclarativeContainer):
    """System module container."""
    config = providers.Configuration()

    # Infrastructure adapters
    system_info_reader = providers.Factory(
        PackageSystemInfoReader,
        package_name="mug",
    )

    # Application handlers
    get_version_handler = providers.Factory(
        GetVersionHandler,
        reader=system_info_reader,
    )

    # Provided by composition root to avoid cross-module leakage
    command_catalog = providers.Dependency(instance_of=CommandCatalog)

    get_help_handler = providers.Factory(
        GetHelpHandler,
        catalog=command_catalog,
    )
