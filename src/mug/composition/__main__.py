"""Composition root CLI entry."""

import typer

from .bootstrap import bootstrap

app = typer.Typer()


def main() -> int:
    """Entry point for the ``mug`` CLI."""
    bootstrap()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
