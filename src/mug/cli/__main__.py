"""
CLI composition root for Mug.

- Loads configuration (env-first, optional JSON overlay via MUG_CONFIG=<path>).
- Builds the DI container and plugs in Common + Module entries.
- Exposes root-level CLI commands and mounts module subcommands.

This mirrors the .NET golden example’s “*Module” entry points by calling
`add_system_module(...)` and `add_documents_module(...)` from each module’s
Infrastructure layer.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import typer

from mug.cli.container import AppContainer
from mug.cli.help_catalog import StaticCommandCatalog

# CA-layer bootstraps (contracts + infrastructure)
from mug.common.application.bootstrap import add_common_application
from mug.common.infrastructure.bootstrap import add_common_infrastructure

# Module composition entries (analogue to IServiceCollection extension methods)
from mug.modules.system.infrastructure.system_module import add_system_module
from mug.modules.documents.infrastructure.documents_module import add_documents_module

# Use case DTOs
from mug.modules.system.application.version.get_version.query import GetVersionQuery


app = typer.Typer(no_args_is_help=True, add_completion=False)


def _load_config() -> dict[str, Any]:
    """Env-first config with optional JSON overlay via MUG_CONFIG=<path>."""
    cfg_path = os.environ.get("MUG_CONFIG", "")
    data: dict[str, Any] = {
        "logging": {"level": os.environ.get("LOG_LEVEL", "INFO")},
        "modules": {
            # documents module DB defaults (ephemeral by default)
            "documents": {"db": {"mode": "ephemeral", "path": None}},
            "system": {},
        },
    }
    if cfg_path and Path(cfg_path).is_file():
        data |= json.loads(Path(cfg_path).read_text())
    return data


def _compose() -> AppContainer:
    """Build DI root, register common + modules, initialize logging."""
    c = AppContainer()
    c.config.from_dict(_load_config())

    # Common bootstraps (contracts first, then infrastructure)
    add_common_application(c)
    add_common_infrastructure(c, log_level=c.config.logging.level())

    # Composition-root–owned catalog (prevents System from knowing other modules)
    catalog = StaticCommandCatalog(
        {
            "documents": ["trace-id", "add", "db"],
        }
    )

    # Plug modules (IServiceCollection-style)
    add_system_module(c, command_catalog=catalog)
    add_documents_module(c)

    # Initialize logging once at startup
    c.logging_initializer().initialize()
    return c


_container = _compose()


@app.callback()
def _root_cb(
    version: bool = typer.Option(
        False, "--version", "-v", is_eager=True, help="Show version and exit."
    )
) -> None:
    if version:
        handler = _container.system().get_version_handler()
        typer.echo(handler.handle(GetVersionQuery()))
        raise typer.Exit(0)


@app.command("version", help="Show version.")
def version_cmd() -> None:
    handler = _container.system().get_version_handler()
    typer.echo(handler.handle(GetVersionQuery()))


@app.command("help", help="Show available module commands.")
def help_cmd() -> None:
    handler = _container.system().get_help_handler()
    typer.echo(handler.handle())


# Mount module CLIs
for subapp in _container.documents().cli_apps():
    app.add_typer(subapp)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
