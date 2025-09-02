from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".importlinter"


def _lint_imports_cmd() -> list[str]:
    """
    Return a command list to invoke the Import Linter CLI ('lint-imports')
    in a way that works on Windows and POSIX, even if PATH isn't set up.

    Priority:
      1) If 'lint-imports' is on PATH, use it.
      2) Otherwise, try <python dir>/Scripts/lint-imports(.exe) on Windows,
         or <python dir>/bin/lint-imports on POSIX.
    """
    cmd = shutil.which("lint-imports")
    if cmd:
        return [cmd]

    py_dir = Path(sys.executable).parent
    if sys.platform.startswith("win"):
        candidate = py_dir / "Scripts" / "lint-imports.exe"
        if candidate.exists():
            return [str(candidate)]
        candidate = py_dir / "Scripts" / "lint-imports"
        if candidate.exists():
            return [str(candidate)]
    else:
        candidate = py_dir / "bin" / "lint-imports"
        if candidate.exists():
            return [str(candidate)]

    raise AssertionError(
        "Cannot find the 'lint-imports' CLI. Make sure you've installed test deps:\n"
        "    pip install -e .[test]\n"
        "and that you're running pytest with the SAME interpreter.\n"
        "If you're not using a venv, ensure your Python Scripts/bin directory is on PATH."
    )


def test_import_linter_contracts_pass_on_clean_tree():
    """
    Baseline: run Import Linter over the repo as-is and expect success.
    """
    assert CONFIG.is_file(), f"Missing .importlinter at {CONFIG}"

    cmd = _lint_imports_cmd() + ["--config", str(CONFIG), "--show-timings"]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "Import Linter failed on clean tree:\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
