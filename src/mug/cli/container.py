"""Application composition root container (DI).

This container only declares provider placeholders. Concrete bindings are
applied by Clean Architecture bootstraps (Common.Application / Common.Infrastructure)
and by per-module registries from the composition root.
"""

from dependency_injector import containers, providers


class AppContainer(containers.DeclarativeContainer):
    # App configuration (dict-like), loaded in the CLI composition step
    config = providers.Configuration()

    # Common services (bound by common.infrastructure.bootstrap)
    clock = providers.Provider()
    logging_initializer = providers.Provider()

    # Module registries (overridden with module containers in the CLI)
    system = providers.Provider()
    documents = providers.Provider()