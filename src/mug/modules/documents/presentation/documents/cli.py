"""Documents.Presentation.Documents: Typer CLI app builder.

Builds the `documents` subcommand group with:
- `trace-id` : generate a new trace/correlation id
- `add`      : compute a deterministic XML path for a new document (no I/O)
- `db` group : lifecycle helpers for the per-module SQLite store
"""

from __future__ import annotations

import json
import typer

from mug.modules.documents.application.documents.get_trace_id.query import GetTraceIdQuery
from mug.modules.documents.application.documents.add_document.command import AddDocumentCommand


def build_documents_app(
    *,
    get_trace_id_handler_factory,
    add_document_handler_factory,
    registry,
):
    """Return a Typer app for the Documents module.

    Args:
        get_trace_id_handler_factory: callable that returns GetTraceIdHandler
        add_document_handler_factory: callable that returns AddDocumentHandler
        registry: module registry instance with DB lifecycle helpers
                  (ensure_storage, engine(), session_factory(), db_path(),
                   drop_storage(), rebuild_storage())
    """
    app = typer.Typer(name="documents", help="Documents module commands")

    @app.command("trace-id", help="Generate a new trace/correlation id.")
    def trace_id() -> None:
        handler = get_trace_id_handler_factory()
        typer.echo(handler.handle(GetTraceIdQuery()))

    @app.command("add", help="Add a new document (stub: prints deterministic XML path).")
    def add(
        title: str = typer.Option(..., "--title", "-t", help="Document title"),
        body: str | None = typer.Option(None, "--body", "-b", help="Optional body"),
    ) -> None:
        handler = add_document_handler_factory()
        result_path = handler.handle(AddDocumentCommand(title=title, body=body))
        typer.echo(json.dumps({"status": "ok", "path": result_path}))

    # ---- DB lifecycle sub-commands ----
    db = typer.Typer(name="db", help="Manage the Documents module SQLite store")

    @db.command("build", help="Create tables/metadata if missing.")
    def db_build() -> None:
        registry.ensure_storage()
        typer.echo("documents DB prepared")

    @db.command("info", help="Show DB path and schema metadata.")
    def db_info() -> None:
        eng = registry.engine()
        Session = registry.session_factory()
        from mug.modules.documents.infrastructure.storage import read_meta  # local to avoid cycles

        with Session() as s:
            meta = read_meta(s)
        typer.echo(json.dumps({"path": str(registry.db_path()), "meta": meta}))

    @db.command("drop", help="Drop the current DB file.")
    def db_drop() -> None:
        # ensure engine is disposed by registry impl
        registry.drop_storage()
        typer.echo("documents DB dropped")

    @db.command("rebuild", help="Drop and recreate the DB.")
    def db_rebuild() -> None:
        registry.rebuild_storage()
        typer.echo("documents DB rebuilt")

    app.add_typer(db)
    return app
