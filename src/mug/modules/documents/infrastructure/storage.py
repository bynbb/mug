"""Documents.Infrastructure: per-module SQLite storage & lifecycle.

This module provides a small, self-contained ORM layer for the Documents module:
- A module-local Declarative Base (no cross-module coupling)
- Minimal models: Document, MugMeta (schema metadata)
- Helpers to create engines/sessions and to prepare/read schema metadata
- Paths & lifecycle helpers for ephemeral/persistent databases

Intended usage from the module registry:
    eng = create_engine_for(str(db_path))
    Session = session_factory_for(eng)
    prepare_schema(eng)        # on first use or explicit "build"
    # ...
    drop_storage(db_path)      # explicit "drop"
    eng = rebuild_storage(db_path)  # "rebuild"
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import String, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, Session, declared_attr, mapped_column, sessionmaker

from mug.common.infrastructure.orm import GUID, UTCDateTime, new_base


# ---------------------------------------------------------------------------
# ORM base & models (module-local)
# ---------------------------------------------------------------------------

Base = new_base()


@dataclass
class _AutoReprMixin:
    """Optional dataclass-like repr for convenience (no behavioral impact)."""

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        fields = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"{self.__class__.__name__}({fields})"


class Document(Base, _AutoReprMixin):
    """Minimal document snapshot table (expand later as needed)."""

    id: Mapped[str] = mapped_column(GUID(), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class MugMeta(Base, _AutoReprMixin):
    """Key-value metadata for the module schema (versioning, timestamps)."""

    __tablename__ = "mug_meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(256), nullable=False)


SCHEMA_VERSION = "1"


# ---------------------------------------------------------------------------
# Engine & session helpers
# ---------------------------------------------------------------------------


def make_sqlite_url(path: str) -> str:
    """Return a SQLAlchemy connection URL for a given file path."""
    if path == ":memory:":
        # Use pysqlite driver for explicit in-memory DB
        return "sqlite+pysqlite:///:memory:"
    return f"sqlite:///{path}"


def create_engine_for(path: str) -> Engine:
    """Create a SQLAlchemy Engine for the given path (no side effects)."""
    return create_engine(make_sqlite_url(path), future=True)


def session_factory_for(engine: Engine):
    """Return a configured session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False, future=True, class_=Session)


# ---------------------------------------------------------------------------
# Schema & metadata
# ---------------------------------------------------------------------------


def prepare_schema(engine: Engine) -> None:
    """Create tables and seed schema metadata if needed."""
    Base.metadata.create_all(bind=engine)

    SessionLocal = session_factory_for(engine)
    with SessionLocal() as s:
        # Seed/refresh minimal metadata
        s.execute(
            text("insert or replace into mug_meta(key,value) values (:k,:v)"),
            [
                {"k": "schema_version", "v": SCHEMA_VERSION},
                {
                    "k": "built_at",
                    "v": datetime.now(tz=timezone.utc).isoformat(),
                },
            ],
        )
        s.commit()


def read_meta(session: Session) -> dict[str, str]:
    """Read all key/value pairs from MugMeta."""
    rows = session.execute(text("select key, value from mug_meta")).all()
    return {k: v for (k, v) in rows}


# ---------------------------------------------------------------------------
# Paths & lifecycle
# ---------------------------------------------------------------------------


def default_ephemeral_path(base_dir: Optional[Path] = None) -> Path:
    """Return a unique ephemeral DB path under .mug/run/documents/."""
    root = (base_dir or Path(".mug") / "run" / "documents")
    root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return (root / f"db-{ts}.sqlite").resolve()


def persistent_path() -> Path:
    """Return the persistent DB path under .mug/data/documents/."""
    root = Path(".mug") / "data" / "documents"
    root.mkdir(parents=True, exist_ok=True)
    return (root / "documents.sqlite").resolve()


def drop_storage(path: Path) -> None:
    """Delete the SQLite file if present (caller must dispose engines)."""
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        # Ensure engine.dispose() was called by the caller before dropping on Windows.
        pass


def rebuild_storage(path: Path) -> Engine:
    """Drop and recreate the storage file, returning a fresh Engine."""
    # Dispose any existing engine for this path (caller responsibility).
    drop_storage(path)
    eng = create_engine_for(str(path))
    prepare_schema(eng)
    return eng