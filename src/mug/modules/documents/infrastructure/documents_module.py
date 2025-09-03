from dependency_injector import providers

from mug.cli.container import AppContainer
from .registry import DocumentsRegistry  # <-- delegate to canonical registry

def add_documents_module(services: AppContainer) -> None:
    """Register the Documents module into the root container."""
    docs = providers.Container(
        DocumentsRegistry,
        config=services.config.modules.documents,
        clock=services.clock,
    )
    services.documents.override(docs)
