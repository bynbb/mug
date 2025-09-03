"""Common.Infrastructure.ORM: Declarative base factory.

Provides `new_base()` which returns a fresh SQLAlchemy DeclarativeBase class
with:
- Stable naming conventions (indexes, FKs, PKs, etc.)
- Automatic snake_case `__tablename__` derived from the class name

Usage (per module):
    from mug.common.infrastructure.orm import new_base

    Base = new_base()

    class Document(Base):
        id: Mapped[str] = mapped_column(GUID(), primary_key=True)
        # -> table name will be "document"
"""

from __future__ import annotations

import re
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr


def _to_snake(name: str) -> str:
    """Convert CamelCase -> snake_case, preserving acronyms reasonably."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.replace("__", "_").lower()


def new_base():
    """Create a new DeclarativeBase with naming conventions and snake_case tables."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix__%(table_name)s__%(column_0_label)s",
            "uq": "uq__%(table_name)s__%(column_0_name)s",
            "ck": "ck__%(table_name)s__%(constraint_name)s",
            "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
            "pk": "pk__%(table_name)s",
        }
    )

    class Base(DeclarativeBase):
        metadata = metadata

        @declared_attr.directive
        def __tablename__(cls) -> str:  # noqa: N805
            return _to_snake(cls.__name__)

    return Base