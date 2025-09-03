# src/mug/modules/documents/infrastructure/registry.py
from __future__ import annotations

from pathlib import Path
from dependency_injector import containers, providers

from mug.common.application.time import Clock
from mug.common.infrastructure.trace_uuid import UuidTraceIdProvider

from mug.modules.documents.infrastructure import storage
from mug.modules.documents.presentation.documents.cli import build_documents_app
from mug.modules.documents.application.documents.get_trace_id.handler import (
    GetTraceIdHandler,
)
from mug.modules.documents.application.documents.add_document.handler import (
    AddDocumentHandler,
)

class DocumentsRegistry(containers.DeclarativeContainer):
    """Documents module container."""
    config = providers.Configuration()

    # ---- DB mode/path -------------------------------------------------------
    db_mode = providers.Callable(
        lambda m: (m or "ephemeral").lower(),
        config.db.mode.optional(),
    )
    db_path = providers.Callable(
        lambda mode, p: Path(p)
        if p
        else (storage.persistent_path() if mode == "persistent" else storage.default_ephemeral_path()),
        db_mode,
        config.db.path.optional(),
    )

    # ---- Engine & session factory ------------------------------------------
    engine = providers.Singleton(lambda path: storage.create_engine_for(str(path)), db_path)
    session_factory = providers.Singleton(lambda eng: storage.session_factory_for(eng), engine)

    # ---- Cross-cutting deps --------------------------------------------------
    clock = providers.Dependency(instance_of=Clock)
    trace_ids = providers.Factory(UuidTraceIdProvider)

    # ---- Application handlers -----------------------------------------------
    get_trace_id_handler = providers.Factory(GetTraceIdHandler, trace_ids=trace_ids)
    add_document_handler = providers.Factory(AddDocumentHandler, clock=clock)

    # ---- Presentation contribution ------------------------------------------
    def cli_apps(self):
        return [
            build_documents_app(
                get_trace_id_handler_factory=self.get_trace_id_handler,
                add_document_handler_factory=self.add_document_handler,
                registry=self,
            )
        ]

    # ---- Storage lifecycle helpers ------------------------------------------
    def ensure_storage(self) -> None:
        storage.prepare_schema(self.engine())

    def drop_storage(self) -> None:
        self.engine().dispose()
        storage.drop_storage(self.db_path())

    def rebuild_storage(self) -> None:
        self.engine().dispose()
        eng = storage.rebuild_storage(self.db_path())
        self.engine.override(providers.Object(eng))
