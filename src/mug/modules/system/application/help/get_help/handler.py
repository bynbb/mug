"""System.Application.Help.GetHelp handler.

Uses the CommandCatalog port to build a human-friendly list of available
module commands. Kept free of Presentation/Infrastructure concerns.
"""

from __future__ import annotations

from mug.modules.system.application.help.ports import CommandCatalog


class GetHelpHandler:
    """Formats a list of module commands from the provided catalog."""

    def __init__(self, catalog: CommandCatalog) -> None:
        self._catalog = catalog

    def handle(self) -> str:
        mapping = self._catalog.list_commands()
        lines: list[str] = ["Available module commands:"]
        for module in sorted(mapping.keys()):
            cmds = [str(c) for c in mapping.get(module, [])]
            lines.append(f"  {module}: {', '.join(cmds) if cmds else '(none)'}")
        return "\n".join(lines)