# Makefile — convenience targets for local dev & CI (portable)
# Works on Windows (cmd.exe), macOS, and Linux.

# ----- Configurable vars -----
PY ?= python
PKG_DIR ?= src
MYPY_CONFIG ?= mypy.ini
IMPORTLINTER_CONFIG ?= .importlinter

# ----- Phony targets -----
.PHONY: default help ruff mypy imports lint test check all-checks clean clean-caches

# Default target (alias for all-checks)
default: all-checks

help:
	@echo "Targets:"
	@echo "  make            - alias for all-checks"
	@echo "  make lint       - ruff + mypy + import-linter (aggregate)"
	@echo "  make ruff       - run ruff"
	@echo "  make mypy       - run mypy"
	@echo "  make imports    - run import-linter"
	@echo "  make test       - run pytest"
	@echo "  make check      - lint + test (fail-fast)"
	@echo "  make all-checks - ruff + mypy + import-linter + pytest"
	@echo "  make clean      - remove caches, dist, build artifacts"
	@echo ""

# ----- Individual tools -----

ruff:
	$(PY) -m ruff check --output-format=github .

mypy:
	$(PY) -m mypy --config-file $(MYPY_CONFIG) $(PKG_DIR)

imports:
	$(PY) -c "import shutil; shutil.rmtree('.import_linter_cache', ignore_errors=True)"
	lint-imports --config $(IMPORTLINTER_CONFIG) --show-timings

test:
	$(PY) -m pytest

# ----- Composed targets -----

lint: ruff mypy imports
check: lint test
all-checks: ruff mypy imports test

# ----- Cleaning targets -----

clean-caches:
	$(PY) -c "import shutil; shutil.rmtree('.pytest_cache', ignore_errors=True)"
	$(PY) -c "import shutil; shutil.rmtree('.import_linter_cache', ignore_errors=True)"
	$(PY) -c "import shutil; shutil.rmtree('__pycache__', ignore_errors=True)"

clean: clean-caches
	$(PY) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ('build','dist')]"
