# tests/conftest.py
from __future__ import annotations
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Path to the repository root."""
    return Path(__file__).resolve().parents[1]

@pytest.fixture(scope="session")
def requirements_dir(repo_root: Path) -> Path:
    """Path to the requirements/ folder used in examples/tests."""
    return repo_root / "requirements"
