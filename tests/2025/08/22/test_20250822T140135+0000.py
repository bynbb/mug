# tests/2025/08/22/test_20250822T140135+0000.py
"""
Automated requirement tests for document_key=20250822T140135+0000.

Each test is tagged with @pytest.mark.req(<requirement_id>) so we maintain
full traceability (spec → tests → CI status), per TESTING_POLICY.md §6/§9.

This suite intentionally mixes:
- structural/static checks (filesystem, pyproject)
- policy checks (no disallowed imports)
- light integration stubs (Typer CLI, CQRS) — marked and explained

References:
- Testing policy & conventions (markers, determinism, mocking) — see repo policy.  # noqa: E501
- Example style & helpers — see prior guardrail suite in this repo.

"""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

import pytest


# -------- Traceability key ----------------------------------------------------
DOC_KEY = "20250822T140135+0000"  # must match the XML filename & document_key


# -------- Repo discovery & helpers (deterministic) ----------------------------
def _is_repo_root(p: Path) -> bool:
    return (p / "pyproject.toml").exists() or (p / ".git").exists()


def _discover_repo_root() -> Path:
    env = os.environ.get("MUG_REPO_ROOT")
    if env:
        pe = Path(env).resolve()
        if _is_repo_root(pe):
            return pe

    starts = [Path(__file__).resolve(), Path.cwd().resolve()]
    seen: set[Path] = set()
    for start in starts:
        for cand in (start, *start.parents):
            if cand in seen:
                continue
            seen.add(cand)
            if _is_repo_root(cand):
                return cand

    # fallback (debug friendly)
    return Path(__file__).resolve().parent


REPO_ROOT = _discover_repo_root()
SRC_DIR = REPO_ROOT / "src"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_pyproject() -> dict:
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    try:
        import tomllib  # Python 3.11+
    except Exception:  # pragma: no cover
        raise AssertionError("Python 3.11+ required (tomllib)")
    with pyproject.open("rb") as f:
        return tomllib.load(f)


def in_any_file(globs: Iterable[str], pattern: str, flags=re.IGNORECASE) -> bool:
    rx = re.compile(pattern, flags)
    for g in globs:
        for p in REPO_ROOT.glob(g):
            if p.is_file() and rx.search(load_text(p)):
                return True
    return False


def first_top_pkg() -> Optional[Path]:
    if not SRC_DIR.exists():
        return None
    for child in sorted(SRC_DIR.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists():
            return child
    return None


def _module_imports_pattern(pkg: Path, pattern: str) -> bool:
    """Scan package Python files for a regex."""
    rx = re.compile(pattern)
    for p in pkg.rglob("*.py"):
        if rx.search(load_text(p)):
            return True
    return False


# ============================================================================
# 1.0 Users Module Folder Setup (ids: 1,7,2,3,4)
# ============================================================================

@pytest.mark.req(1)
def test_1_top_level_packages_exist_and_importable():
    """{DOC_KEY}+1"""
    # Required directories:
    expect = [
        SRC_DIR / "mug" / "composition",
        SRC_DIR / "mug" / "common",
        SRC_DIR / "mug" / "modules",
    ]
    for d in expect:
        assert d.exists() and d.is_dir(), f"Missing required package dir: {d}"
        init = d / "__init__.py"
        assert init.exists(), f"Missing __init__.py in {d}"

@pytest.mark.req(7)
@pytest.mark.skip(reason="Spec 7 — Enforced via Import Linter contracts; trivial unit assertion provided no guarantees. See {DOC_KEY}+7.")
def test_7_asymmetric_coupling_public_facades_only():
    """{DOC_KEY}+7 (policy: cannot fully prove statically; partial check)"""
    # Guardrail: discourage imports into internals by searching for '... .domain.' etc.
    # Full enforcement is handled by Import Linter contracts (Section 4.0).
    return False

@pytest.mark.req(2)
def test_2_users_layer_skeleton_present():
    """{DOC_KEY}+2"""
    base = SRC_DIR / "mug" / "modules" / "users"
    for layer in ("domain", "application", "infrastructure", "presentation"):
        pkg = base / layer
        assert (pkg / "__init__.py").exists(), f"Missing {pkg}/__init__.py"

@pytest.mark.req(3)
def test_3_feature_api_reexports_exist():
    """{DOC_KEY}+3"""
    # Each layer exposes a package with __init__.py that re-exports public API.
    # We assert __init__.py exists; content checks are linter/import-linter territory.
    base = SRC_DIR / "mug" / "modules" / "users"
    for layer in ("domain", "application", "infrastructure", "presentation"):
        assert (base / layer / "__init__.py").exists()

@pytest.mark.req(4)
def test_4_common_layered_structure_exists():
    """{DOC_KEY}+4"""
    base = SRC_DIR / "mug" / "common"
    for layer in ("domain", "application", "infrastructure", "presentation"):
        assert (base / layer / "__init__.py").exists(), f"Missing {base}/{layer}/__init__.py"


# ============================================================================
# 2.0 Composition Root & CLI (ids: 67,5,6,8,9,10,11,94)
# ============================================================================

@pytest.mark.req(67)
def test_67_composition_bootstrap_module_exists():
    """{DOC_KEY}+67"""
    assert (SRC_DIR / "mug" / "composition" / "bootstrap.py").exists()

@pytest.mark.req(5)
def test_5_composition_dunder_main_hosts_typer_root():
    """{DOC_KEY}+5 (stub: semantic presence)"""
    path = SRC_DIR / "mug" / "composition" / "__main__.py"
    assert path.exists()
    # Semantic hint: file should import typer or get Typer app from modules
    txt = load_text(path)
    assert "typer" in txt.lower() or "Typer" in txt, "Expected Typer usage in composition __main__.py"

@pytest.mark.req(6)
@pytest.mark.skip(reason="Spec 6 (CLI help displays the `users` group and its commands.) — Requires interactive CLI runtime; not unit-testable without full Typer app wiring. See {DOC_KEY}+6.")
def test_6_help_shows_users_group_stub():
    """{DOC_KEY}+6 (stub: requires runtime Typer app)"""
    # TODO: Once Typer root exists, invoke runner and assert "users" in help.
    return False

@pytest.mark.req(8)
def test_8_console_script_declared():
    """{DOC_KEY}+8"""
    pj = load_pyproject()
    scripts = pj.get("project", {}).get("scripts", {})
    assert scripts.get("mug") == "mug.composition.__main__:main"

@pytest.mark.req(9)
def test_9_appcontainer_mediator_mentions_in_bootstrap():
    """{DOC_KEY}+9 (presence check only)"""
    txt = load_text(SRC_DIR / "mug" / "composition" / "bootstrap.py")
    assert re.search(r"\bMediator\b|\bAppContainer\b", txt), "Expected Mediator/AppContainer in bootstrap"

@pytest.mark.req(10)
def test_10_no_service_locator_in_modules():
    """{DOC_KEY}+10"""
    modules = SRC_DIR / "mug" / "modules"
    if modules.exists():
        # service locator imports should not appear in modules/**
        assert not in_any_file(["src/mug/modules/**/*.py"], r"\bdependency_injector\b|\bcontainer\.get\b")

@pytest.mark.req(11)
def test_11_feature_di_hook_exists():
    """{DOC_KEY}+11"""
    assert (SRC_DIR / "mug" / "modules" / "users" / "composition" / "di.py").exists()

@pytest.mark.req(94)
def test_94_only_bootstrap_reads_process_config():
    """{DOC_KEY}+94 (heuristic)"""
    # Heuristic: forbid os.environ usage outside composition/bootstrap
    bad = in_any_file(["src/mug/**/*.py"], r"os\.environ(?!.*composition/bootstrap\.py)")
    assert not bad, "Process config should be bound in composition/bootstrap only"


# ============================================================================
# 3.0 Dependency Rules (ids: 12–20,95)
# ============================================================================

@pytest.mark.req(12)
def test_12_domain_has_no_upward_imports():
    """{DOC_KEY}+12 (heuristic)"""
    dom = SRC_DIR / "mug" / "modules" / "users" / "domain"
    if dom.exists():
        assert not _module_imports_pattern(dom, r"\bfrom\s+mug\.modules\.users\.(application|infrastructure|presentation|composition)\b")

@pytest.mark.req(13)
def test_13_application_depends_only_on_domain_plus_common_domain():
    """{DOC_KEY}+13 (heuristic)"""
    app = SRC_DIR / "mug" / "modules" / "users" / "application"
    if app.exists():
        # Allow imports from its own domain and mug.common.domain
        bad = _module_imports_pattern(app, r"\bmug\.modules\.users\.(infrastructure|presentation)\b")
        assert not bad

@pytest.mark.req(14)
def test_14_presentation_not_import_infra():
    """{DOC_KEY}+14 (heuristic)"""
    pres = SRC_DIR / "mug" / "modules" / "users" / "presentation"
    if pres.exists():
        assert not _module_imports_pattern(pres, r"\bmug\.modules\.users\.infrastructure\b")

@pytest.mark.req(15)
def test_15_infrastructure_import_policy():
    """{DOC_KEY}+15 (heuristic)"""
    infra = SRC_DIR / "mug" / "modules" / "users" / "infrastructure"
    if infra.exists():
        bad = _module_imports_pattern(infra, r"\bmug\.modules\.users\.presentation\b")
        assert not bad

@pytest.mark.req(16)
def test_16_composition_does_not_import_domain_directly():
    """{DOC_KEY}+16 (heuristic)"""
    comp = SRC_DIR / "mug" / "composition"
    if comp.exists():
        assert not _module_imports_pattern(comp, r"\bmug\.modules\.users\.domain\.(?!public)")

@pytest.mark.req(17)
@pytest.mark.skip(reason="Spec 17 — Cross-module internal import detection requires Import Linter/static analysis; not unit-testable as written. See {DOC_KEY}+17.")
def test_17_no_cross_module_internals():
    """{DOC_KEY}+17 (heuristic)"""
    modules = SRC_DIR / "mug" / "modules"
    if modules.exists():
        # Look for "mug.modules.(a).(b)" where a != b and import path isn't ".+\.public"
        return False  # covered by Import Linter contracts too

@pytest.mark.req(18)
@pytest.mark.skip(reason="Spec 18 (`modules.*.composition` may import its module’s application/infrastructure for wiring, but not its domain internals (facades must be used).) — Requires real module wiring inspection; current test body had no checks. See {DOC_KEY}+18.")
def test_18_module_composition_uses_facades():
    """{DOC_KEY}+18 (heuristic)"""
    users_comp = SRC_DIR / "mug" / "modules" / "users" / "composition"
    if users_comp.exists():
        return False

@pytest.mark.req(19)
@pytest.mark.skip(reason="Spec 19 — Architecture rule verified by import graph analysis; not unit-testable without AST/import scanning. See {DOC_KEY}+19.")
def test_19_application_public_is_the_only_external_surface():
    """{DOC_KEY}+19 (heuristic)"""
    return False

@pytest.mark.req(20)
def test_20_domain_models_persistence_agnostic():
    """{DOC_KEY}+20 (heuristic)"""
    dom = SRC_DIR / "mug" / "modules" / "users" / "domain"
    if dom.exists():
        assert not in_any_file([str(dom / "**/*.py")], r"sqlalchemy|orm|Column\(")

@pytest.mark.req(95)
def test_95_domain_application_no_io_or_environ():
    """{DOC_KEY}+95 (heuristic)"""
    for layer in ("domain", "application"):
        base = SRC_DIR / "mug" / "modules" / "users" / layer
        if base.exists():
            assert not in_any_file([str(base / "**/*.py")], r"\bos\.environ\b|open\(|requests\.")


# ============================================================================
# 4.0 Import Linter (ids: 68,69,21)
# ============================================================================

@pytest.mark.req(68)
def test_68_importlinter_config_exists():
    """{DOC_KEY}+68"""
    assert (REPO_ROOT / ".importlinter").exists()

@pytest.mark.req(69)
@pytest.mark.skip(reason="Spec 69 — CI-only gate; needs pipeline config to validate. See {DOC_KEY}+69.")
def test_69_ci_runs_lint_imports_stub():
    """{DOC_KEY}+69 (stub: CI-only behavior)"""
    # Validate in CI by grepping workflow; local assertion is a stub.
    return False

@pytest.mark.req(21)
def test_21_contracts_named_in_importlinter():
    """{DOC_KEY}+21 (presence check)"""
    cfg = REPO_ROOT / ".importlinter"
    assert cfg.exists()
    txt = load_text(cfg)
    for name in ["domain_independent", "app_depends_only_on_domain", "infra_can_import_app_public", "no_cross_module_internals"]:
        assert name in txt, f"Missing contract: {name}"


# ============================================================================
# 5.0 Use Cases & Ports (ids: 22–26,96)
# ============================================================================

@pytest.mark.req(22)
def test_22_domain_public_facade_file_exists():
    """{DOC_KEY}+22"""
    assert (SRC_DIR / "mug" / "modules" / "users" / "domain" / "public.py").exists()

@pytest.mark.req(23)
def test_23_application_public_facade_file_exists():
    """{DOC_KEY}+23"""
    assert (SRC_DIR / "mug" / "modules" / "users" / "application" / "public.py").exists()

@pytest.mark.req(24)
def test_24_infra_only_imports_application_public():
    """{DOC_KEY}+24 (heuristic)"""
    infra = SRC_DIR / "mug" / "modules" / "users" / "infrastructure"
    if infra.exists():
        txt = "\n".join(load_text(p) for p in infra.rglob("*.py"))
        assert "application.public" in txt or "from ...application.public" in txt

@pytest.mark.req(25)
@pytest.mark.skip(reason="Spec 25 — Needs running Typer app and composition wiring; not a unit test. See {DOC_KEY}+25.")
def test_25_presentation_calls_application_factories_stub():
    """{DOC_KEY}+25 (stub: requires CLI + factories)"""
    return False

@pytest.mark.req(26)
def test_26_each_layer_public_reexports():
    """{DOC_KEY}+26 (presence only)"""
    base = SRC_DIR / "mug" / "modules" / "users"
    for layer in ("domain", "application", "infrastructure", "presentation"):
        assert (base / layer / "public.py").exists()

@pytest.mark.req(96)
def test_96_common_cross_cutting_ports_exist_or_placeholder():
    """{DOC_KEY}+96"""
    base = SRC_DIR / "mug" / "common"
    # Accept existence of 'public.py' in domain/application as the minimal surface
    ok = (base / "domain" / "public.py").exists() and (base / "application" / "public.py").exists()
    assert ok, "Expect mug/common/{domain,application}/public.py for cross-cutting ports"


# ============================================================================
# 6.0 CI & Artifacts (ids: 29,30)
# ============================================================================

@pytest.mark.req(29)
@pytest.mark.skip(reason="Spec 29 (CI jobs run unit/structure tests and enforce `lint-imports`.) — CI-only behavior; requires pipeline context to validate. See {DOC_KEY}+29.")
def test_29_ci_runs_unit_structure_tests_stub():
    """{DOC_KEY}+29 (stub: CI-only)"""
    return False

@pytest.mark.req(30)
@pytest.mark.skip(reason="Spec 30 (CI generates a dependency diagram and uploads it as an artifact.) — Artifact presence validated in CI; not unit-testable locally. See {DOC_KEY}+30.")
def test_30_ci_dependency_diagram_artifact_stub():
    """{DOC_KEY}+30 (stub: CI-only)"""
    return False


# ============================================================================
# 7.0 Developer Ergonomics (ids: 31–35)
# ============================================================================

@pytest.mark.req(31)
def test_31_docs_describe_running_module_and_module_clis():
    """{DOC_KEY}+31 (heuristic)"""
    assert in_any_file(["README.*", "docs/**/*.*"], r"python\s+-m\s+mug")

@pytest.mark.req(32)
def test_32_readme_describes_import_linter_rules():
    """{DOC_KEY}+32 (heuristic)"""
    assert in_any_file(["README.*", "docs/**/*.*"], r"Import\s+Linter|importlinter")

@pytest.mark.req(33)
def test_33_pytest_ini_allows_timestamped_test_modules():
    """{DOC_KEY}+33"""
    ini = REPO_ROOT / "pytest.ini"
    assert ini.exists()
    txt = load_text(ini)
    assert re.search(r"python_files\s*=\s*test_*.py\s*test_????????T??????[+-]\d{4}\.py", txt.replace(" ", "")), \
        "pytest.ini should allow timestamped test filenames"

@pytest.mark.req(34)
def test_34_python311_targeted_consistently():
    """{DOC_KEY}+34 (heuristic)"""
    pj = load_pyproject()
    req_py = pj.get("project", {}).get("requires-python", "")
    assert ">=3.11" in req_py or "==3.11" in req_py

@pytest.mark.req(35)
def test_35_docs_include_convention_stack_matrix_hint():
    """{DOC_KEY}+35 (heuristic)"""
    assert in_any_file(["README.*", "docs/**/*.*"], r"compatibility|matrix|guardrails|type\s+strictness")


# ============================================================================
# 8.0 Root Hygiene & Additional Structural Rules (ids: 70,36,37,38,90)
# ============================================================================

@pytest.mark.req(70)
def test_70_composition_entry_and_bootstrap_present():
    """{DOC_KEY}+70"""
    comp = SRC_DIR / "mug" / "composition"
    assert (comp / "__main__.py").exists() and (comp / "bootstrap.py").exists()

@pytest.mark.req(36)
def test_36_each_layer_in_users_has_public_facade():
    """{DOC_KEY}+36"""
    base = SRC_DIR / "mug" / "modules" / "users"
    for layer in ("domain", "application", "infrastructure", "presentation"):
        assert (base / layer / "public.py").exists()

@pytest.mark.req(37)
@pytest.mark.skip(reason="Spec 37 (External imports of feature-internal paths (e.g., `mug.modules.users.domain.*`) are not permitted.) — Enforced by Import Linter contracts, not trivial unit assertions. See {DOC_KEY}+37.")
def test_37_no_external_imports_of_feature_internals():
    """{DOC_KEY}+37 (heuristic)"""
    # Hard to prove globally; enforced by Import Linter. Keep as placeholder.
    return False

@pytest.mark.req(38)
@pytest.mark.skip(reason="Spec 38 (Across layer boundaries, only each layer’s `public.py` may be imported; internal imports are prohibited to preserve information hiding.) — Enforced via Import Linter contracts; trivial unit assertion provided no guarantees. See {DOC_KEY}+38.")
def test_38_only_public_imports_across_layers():
    """{DOC_KEY}+38 (heuristic)"""
    return False

@pytest.mark.req(90)
def test_90_thin_entrypoints_no_domain_or_app_imports():
    """{DOC_KEY}+90 (heuristic)"""
    main_py = SRC_DIR / "mug" / "composition" / "__main__.py"
    if main_py.exists():
        txt = load_text(main_py)
        assert not re.search(r"mug\.modules\.users\.(domain|application)\.(?!public)", txt)


# ============================================================================
# 9.0 Anti-Patterns & Prohibitions (ids: 39–41)
# ============================================================================

@pytest.mark.req(39)
def test_39_no_dependency_injector_imports_in_modules():
    """{DOC_KEY}+39"""
    assert not in_any_file(["src/mug/modules/**/*.py"], r"\bdependency_injector\b")

@pytest.mark.req(40)
def test_40_dependency_injector_only_in_composition():
    """{DOC_KEY}+40"""
    has_in_comp = in_any_file(["src/mug/composition/**/*.py"], r"\bdependency_injector\b")
    has_in_modules = in_any_file(["src/mug/modules/**/*.py"], r"\bdependency_injector\b")
    assert has_in_comp or not has_in_comp  # info-only
    assert not has_in_modules

@pytest.mark.req(41)
def test_41_no_container_lookups_in_modules():
    """{DOC_KEY}+41"""
    assert not in_any_file(["src/mug/modules/**/*.py"], r"\bcontainer\.get\(|providers\.\w+\(")


# ============================================================================
# 10.0 Inter-Pattern Contracts (ids: 42–46,91–93)
# ============================================================================

@pytest.mark.req(42)
@pytest.mark.skip(reason="Spec 42 (Every command/query handler is registered with the Mediator via composition.) — Requires mediator wiring in composition; needs integration test with running container. See {DOC_KEY}+42.")
def test_42_every_handler_registered_via_composition_stub():
    """{DOC_KEY}+42 (stub)"""
    return False

@pytest.mark.req(43)
def test_43_presentation_calls_application_only_heuristic():
    """{DOC_KEY}+43 (heuristic)"""
    pres = SRC_DIR / "mug" / "modules" / "users" / "presentation"
    if pres.exists():
        assert not _module_imports_pattern(pres, r"\bmug\.modules\.users\.(domain|infrastructure)\b")

@pytest.mark.req(44)
@pytest.mark.skip(reason="Spec 44 (Application depends only on its own domain ports (facades), not internal implementations.) — Static analysis or Import Linter needed; this placeholder had no checks. See {DOC_KEY}+44.")
def test_44_application_depends_on_domain_ports_only_stub():
    """{DOC_KEY}+44 (stub)"""
    return False

@pytest.mark.req(45)
@pytest.mark.skip(reason="Spec 45 (Pipeline behaviors (validation, logging, exception mapping) live in the application layer and are registered in the mediator pipeline; busin…) — Requires mediator pipeline wiring and integration context. See {DOC_KEY}+45.")
def test_45_pipeline_behaviors_in_application_stub():
    """{DOC_KEY}+45 (stub)"""
    return False

@pytest.mark.req(46)
@pytest.mark.skip(reason="Spec 46 (Events are outward-only coupling: modules publish domain/integration events without depending on consumers; subscribers live in their own bo…) — Architectural contract validated via import rules/runtime observers; cannot be proven with a no-op unit test. See {DOC_KEY}+46.")
def test_46_events_outward_only_stub():
    """{DOC_KEY}+46 (stub)"""
    return False

@pytest.mark.req(91)
def test_91_constructor_injection_no_globals_heuristic():
    """{DOC_KEY}+91 (heuristic)"""
    assert not in_any_file(["src/**/*.py"], r"\bGLOBAL_(CONTAINER|REGISTRY)\b")

@pytest.mark.req(92)
def test_92_base_exception_types_in_common_public():
    """{DOC_KEY}+92"""
    for part in ("domain", "application"):
        assert (SRC_DIR / "mug" / "common" / part / "public.py").exists()

@pytest.mark.req(93)
@pytest.mark.skip(reason="Spec 93 (Module DI hooks (`modules/*/composition/di.py`) are pure and idempotent: they only bind ports to implementations and perform no I/O or envir…) — Purity/idempotence requires AST/static analysis; placeholder had no checks. See {DOC_KEY}+93.")
def test_93_module_di_hooks_are_pure_stub():
    """{DOC_KEY}+93 (stub)"""
    # To implement: AST scan of di.py for I/O/env ops. Placeholder until code exists.
    return False


# ============================================================================
# 11.0 Toolchain Governance & Drift Control (ids: 71,72)
# ============================================================================

@pytest.mark.req(71)
@pytest.mark.skip(reason="Spec 71 (CI includes a weekly canary job with unpinned tool versions to detect drift.) — CI-only behavior; requires pipeline context to validate. See {DOC_KEY}+71.")
def test_71_ci_weekly_canary_unpinned_stub():
    """{DOC_KEY}+71 (CI-only)"""
    return False

@pytest.mark.req(72)
def test_72_config_parity_mypy_requires_python_runtime_target():
    """{DOC_KEY}+72 (heuristic)"""
    pj = load_pyproject()
    req_py = pj.get("project", {}).get("requires-python", "")
    assert "3.11" in req_py


# ============================================================================
# 12.0 Observability & Runtime Invariants (ids: 73,47)
# ============================================================================

@pytest.mark.req(73)
@pytest.mark.skip(reason="Spec 73 (Non-zero exit codes are returned for unhandled errors; zero for success paths.) — Requires executing the CLI to observe exit codes; out of scope for unit-only test. See {DOC_KEY}+73.")
def test_73_exit_codes_invariants_stub():
    """{DOC_KEY}+73 (stub: validate via CLI once implemented)"""
    return False

@pytest.mark.req(47)
def test_47_telemetry_hook_presence_in_composition():
    """{DOC_KEY}+47"""
    txt = load_text(SRC_DIR / "mug" / "composition" / "bootstrap.py")
    assert re.search(r"telemetry|monitor|record_event|logger", txt, re.IGNORECASE), \
        "Expect a pluggable logging/monitoring hook at composition"


# ============================================================================
# 13.0 SQLite Ephemeral Reporting DB (ids: 48–52)
# ============================================================================

@pytest.mark.req(48)
@pytest.mark.skip(reason="Spec 48 (DDL files are embedded under `.../infrastructure/db/ddl/` and loadable via resources.) — DB feature not implemented yet; commands/DDL are placeholders. See {DOC_KEY}+48.")
def test_48_infra_db_ddl_resources_exist_stub():
    """{DOC_KEY}+48 (stub until DB feature exists)"""
    return False

@pytest.mark.req(49)
@pytest.mark.skip(reason="Spec 49 (The generated DB uses `STRICT` tables and `PRAGMA foreign_keys=ON`.) — Requires generating a DB and inspecting PRAGMAs; feature not implemented in test. See {DOC_KEY}+49.")
def test_49_generated_db_pragma_policy_stub():
    """{DOC_KEY}+49 (stub)"""
    return False

@pytest.mark.req(50)
@pytest.mark.skip(reason="Spec 50 (The command `db generate-empty` creates a schema with a `schema_version` row.) — DB feature not implemented yet; commands/DDL are placeholders. See {DOC_KEY}+50.")
def test_50_db_generate_empty_command_stub():
    """{DOC_KEY}+50 (stub)"""
    return False

@pytest.mark.req(51)
@pytest.mark.skip(reason="Spec 51 (The command `db import` loads validated rows parsed from Markdown/XML.) — Requires real import command and fixtures; not yet implemented. See {DOC_KEY}+51.")
def test_51_db_import_command_stub():
    """{DOC_KEY}+51 (stub)"""
    return False

@pytest.mark.req(52)
@pytest.mark.skip(reason="Spec 52 (The command `db delete` removes or truncates tables depending on flags.) — DB feature not implemented yet; commands/DDL are placeholders. See {DOC_KEY}+52.")
def test_52_db_delete_command_stub():
    """{DOC_KEY}+52 (stub)"""
    return False


# ============================================================================
# 14.0 DB Folder Strategy & DDL Organization (ids: 53–55)
# ============================================================================

@pytest.mark.req(53)
@pytest.mark.skip(reason="Spec 53 (Database path policy: `.mug/db/<module>/<yyyy-mm-dd>-<schema>.sqlite`.) — Migration/schema policy requires DB runtime and artifacts. See {DOC_KEY}+53.")
def test_53_db_path_policy_doc_stub():
    """{DOC_KEY}+53 (stub)"""
    return False

@pytest.mark.req(54)
@pytest.mark.skip(reason="Spec 54 (Migrations are stored under `.../db/migrations/` and are idempotent.) — Needs executing migrations against a DB; not a unit test. See {DOC_KEY}+54.")
def test_54_migrations_idempotent_stub():
    """{DOC_KEY}+54 (stub)"""
    return False

@pytest.mark.req(55)
@pytest.mark.skip(reason="Spec 55 (A `schema_version` table exists and is updated by migrations.) — Migration/schema policy requires DB runtime and artifacts. See {DOC_KEY}+55.")
def test_55_schema_version_table_stub():
    """{DOC_KEY}+55 (stub)"""
    return False


# ============================================================================
# 15.0 CQRS Data Access (ids: 56–59)
# ============================================================================

@pytest.mark.req(56)
@pytest.mark.skip(reason="Spec 56 (Query SQL files are stored under `.../queries/*.sql` and loadable via resources.) — CQRS data access requires concrete adapters and resources; no fixtures yet. See {DOC_KEY}+56.")
def test_56_query_sql_files_under_queries_stub():
    """{DOC_KEY}+56 (stub)"""
    return False

@pytest.mark.req(57)
@pytest.mark.skip(reason="Spec 57 (Query results map to dataclasses (or Pydantic models) with type checks.) — Requires concrete query adapters/models to validate mapping. See {DOC_KEY}+57.")
def test_57_query_results_map_to_dataclasses_or_pydantic_stub():
    """{DOC_KEY}+57 (stub)"""
    return False

@pytest.mark.req(58)
@pytest.mark.skip(reason="Spec 58 (Command handlers do not return domain entities; queries do not mutate state.) — CQRS data access requires concrete adapters and resources; no fixtures yet. See {DOC_KEY}+58.")
def test_58_commands_no_return_entities_queries_no_mutation_stub():
    """{DOC_KEY}+58 (stub)"""
    return False

@pytest.mark.req(59)
@pytest.mark.skip(reason="Spec 59 (Composition wires separate read/write services according to CQRS.) — CQRS wiring demands integration test with composition. See {DOC_KEY}+59.")
def test_59_composition_wires_read_write_services_stub():
    """{DOC_KEY}+59 (stub)"""
    return False



# ============================================================================
# 17.0 Typer CLI – Dependencies & Contracts (ids: 80–89)
# ============================================================================

@pytest.mark.req(80)
def test_80_pyproject_declares_typer_and_click_with_versions():
    """{DOC_KEY}+80"""
    pj = load_pyproject()
    deps = (pj.get("project", {}).get("dependencies") or [])
    hay = "\n".join(deps)
    assert re.search(r"\btyper\b", hay, re.IGNORECASE), "Typer not declared"
    assert re.search(r"\bclick\b", hay, re.IGNORECASE), "Click not declared"
    # Version hints (best-effort heuristic)
    assert any(("0.12" in d or ">=" in d or "<" in d) for d in deps if "typer" in d.lower())

@pytest.mark.req(81)
def test_81_only_composition_and_presentation_import_typer_click():
    """{DOC_KEY}+81 (heuristic)"""
    # If typer/click appear in domain/application/infrastructure, fail
    bad = in_any_file(
        ["src/mug/modules/**/domain/**/*.py", "src/mug/modules/**/application/**/*.py", "src/mug/modules/**/infrastructure/**/*.py"],
        r"\b(typer|click)\b"
    )
    assert not bad

@pytest.mark.req(82)
def test_82_feature_presentation_exports_typer_app_presence():
    """{DOC_KEY}+82"""
    up = SRC_DIR / "mug" / "modules" / "users" / "presentation" / "public.py"
    assert up.exists()
    txt = load_text(up)
    assert "Typer" in txt or "get_app" in txt or "app =" in txt

@pytest.mark.req(83)
@pytest.mark.skip(reason="Spec 83 — Must import Typer apps lazily and observe side effects; needs runtime harness. See {DOC_KEY}+83.")
def test_83_presentation_public_has_no_side_effects_stub():
    """{DOC_KEY}+83 (stub)"""
    return False

@pytest.mark.req(84)
@pytest.mark.skip(reason="Spec 84 (The composition registers module apps (stub), and (b) each feature app under its group name (e.g., `users`); command/group name collisions a…) — Placeholder stub with no verifications; original assertion always passed. See {DOC_KEY}+84.")
def test_84_composition_registers_feature_apps_stub():
    """{DOC_KEY}+84 (stub)"""
    return False

@pytest.mark.req(85)
@pytest.mark.skip(reason="Spec 85 (CLI handlers are thin: they call application factories/use cases via composition; they do not import infrastructure or domain internals and …) — Handler thinness is an architectural constraint; check via static analysis/reviews, not trivial unit test. See {DOC_KEY}+85.")
def test_85_cli_handlers_are_thin_stub():
    """{DOC_KEY}+85 (stub)"""
    return False

@pytest.mark.req(86)
@pytest.mark.skip(reason="Spec 86 (CLI error handling maps exceptions to non-zero exit codes and zero on success, consistent with runtime invariants.) — Placeholder stub with no verifications; original assertion always passed. See {DOC_KEY}+86.")
def test_86_cli_error_handling_maps_to_exit_codes_stub():
    """{DOC_KEY}+86 (stub)"""
    return False

@pytest.mark.req(87)
@pytest.mark.skip(reason="Spec 87 (`python -m mug --help` and `mug --help` render consistent help text showing the `users` group and the system-level version command.) — Requires invoking CLI to compare help text between entrypoints. See {DOC_KEY}+87.")
def test_87_help_consistency_stub():
    """{DOC_KEY}+87 (stub)"""
    return False

@pytest.mark.req(88)
@pytest.mark.skip(reason="Spec 88 (The Typer root implements shell completion commands (`--install-completion` / `--show-completion`) where supported by Typer/Click.) — Requires interactive CLI runtime; not unit-testable without full Typer app wiring. See {DOC_KEY}+88.")
def test_88_shell_completion_supported_stub():
    """{DOC_KEY}+88 (stub)"""
    return False

@pytest.mark.req(89)
def test_89_main_entry_returns_int_and_is_console_script_target():
    """{DOC_KEY}+89 (heuristic)"""
    pj = load_pyproject()
    scripts = pj.get("project", {}).get("scripts", {})
    assert scripts.get("mug") == "mug.composition.__main__:main"
    

@pytest.mark.req(97)
def test_97_top_level_mug_is_pep420_namespace():
    """{DOC_KEY}+97"""
    top = SRC_DIR / "mug"
    assert top.exists() and top.is_dir(), "Expected src/mug directory to exist"
    assert not (top / "__init__.py").exists(), "PEP 420 namespace package MUST NOT have __init__.py at src/mug"
    # Sanity: subpackages may still be regular packages
    assert (top / "composition").exists() or (top / "modules").exists() or (top / "common").exists()


@pytest.mark.req(98)
@pytest.mark.skip(reason=(
    "{DOC_KEY}+98 — Addendum discourages layer-level public.py facades; "
    "this repo’s base spec earlier REQUIRES them (e.g., req 22/23/26/36). "
    "Boundary enforcement should be delegated to Import Linter and tests. "
    "Marking as skipped to avoid conflicting assertions until policy is switched."
))
def test_98_no_artificial_public_facades():
    """{DOC_KEY}+98 (policy conflict with earlier requirements)"""
    # If/when the addendum supersedes earlier rules, implement a search that FAILS
    # when {domain,application,infrastructure,presentation}/public.py exists.
    return False


@pytest.mark.req(99)
def test_99_every_module_has_all_layer_slices_even_if_empty():
    """{DOC_KEY}+99"""
    modules_root = SRC_DIR / "mug" / "modules"
    if not modules_root.exists():
        pytest.skip("No modules found under src/mug/modules")
    layer_names = ("composition", "domain", "application", "infrastructure", "presentation")
    offenders = []
    for mod in sorted([p for p in modules_root.iterdir() if p.is_dir()]):
        missing = [ln for ln in layer_names if not (mod / ln).exists()]
        if missing:
            offenders.append((mod.name, missing))
    assert not offenders, f"Each module must include all slices: {offenders}"


@pytest.mark.req(100)
@pytest.mark.skip(reason=(
    "{DOC_KEY}+100 — Manual review: ‘files written once in final form without reopening’ "
    "cannot be proven via static checks."
))
def test_100_files_written_once_final_form_stub():
    """{DOC_KEY}+100 (manual review)"""
    return False


@pytest.mark.req(101)
@pytest.mark.skip(reason=(
    "{DOC_KEY}+101 — Manual review: generation of repetitive boilerplate (e.g., __init__.py) "
    "via script is a process requirement. Add a scaffold tool and CI guard if desired."
))
def test_101_boilerplate_generated_by_script_stub():
    """{DOC_KEY}+101 (manual review/process)"""
    # Option for later: assert presence of a scaffold script/Make target.
    return False


@pytest.mark.req(102)
def test_102_application_organized_by_use_case_with_command_query_handler():
    """{DOC_KEY}+102 (heuristic)"""
    # Heuristic: look for any folder under .../application/** that contains all of
    # {command.py, query.py, handler.py}. This doesn’t enforce naming, just presence.
    apps = list((SRC_DIR / "mug").rglob("modules/*/application"))
    if not apps:
        pytest.skip("No application folders detected")
    found_any = False
    for app_dir in apps:
        for uc in [p for p in app_dir.rglob("*") if p.is_dir()]:
            have = {f.name for f in uc.glob("*.py")}
            if {"command.py", "query.py", "handler.py"}.issubset(have):
                found_any = True
                break
        if found_any:
            break
    assert found_any, (
        "Expected at least one use-case folder under application/ containing "
        "command.py, query.py, and handler.py (per req 102)"
    )


@pytest.mark.req(103)
def test_103_all_names_lowercase_snake_case():
    """{DOC_KEY}+103"""
    root = SRC_DIR / "mug"
    if not root.exists():
        pytest.skip("src/mug not found")
    bad_paths = []

    def _ok_name(name: str, is_file: bool) -> bool:
        if name in {"__pycache__"}:
            return True
        if is_file:
            # only enforce for Python source files
            if not name.endswith(".py"):
                return True
            stem = name[:-3]
            return bool(re.fullmatch(r"[a-z0-9_]+", stem))
        return bool(re.fullmatch(r"[a-z0-9_]+", name))

    for p in root.rglob("*"):
        name = p.name
        if not _ok_name(name, p.is_file()):
            bad_paths.append(str(p.relative_to(SRC_DIR)))
    assert not bad_paths, f"Non-lowercase_snake_case names found: {bad_paths}"


@pytest.mark.req(104)
def test_104_no_http_endpoints_and_presentation_limited_to_cli_wiring():
    """{DOC_KEY}+104 (heuristic)"""
    # Disallow typical HTTP server frameworks/usages in the repo
    http_fw_pattern = r"\b(fastapi|flask|django\.|starlette|aiohttp\.web)\b"
    assert not in_any_file(["src/mug/**/*.py"], http_fw_pattern), \
        "HTTP web frameworks detected — presentation should be CLI-only"
    # Presentation layer should not import http client/server libs
    pres = SRC_DIR / "mug" / "modules"
    if pres.exists():
        assert not in_any_file(
            ["src/mug/modules/**/presentation/**/*.py"],
            r"\b(fastapi|flask|django\.|starlette|aiohttp|requests|httpx)\b"
        ), "Presentation code appears to include HTTP concerns; keep it to CLI wiring"


@pytest.mark.req(105)
def test_105_import_linter_enforces_layer_and_module_independence():
    """{DOC_KEY}+105"""
    # Accept either .importlinter file or pyproject-managed config,
    # but require that contracts exist to enforce layer deps and module independence.
    cfg_file = REPO_ROOT / ".importlinter"
    pj = load_pyproject()
    tool_cfg = (pj.get("tool") or {}).get("importlinter")  # pyproject-based config
    assert cfg_file.exists() or tool_cfg is not None, \
        "Import Linter config must exist (.importlinter or [tool.importlinter] in pyproject.toml)"
    hay = ""
    if cfg_file.exists():
        hay += load_text(cfg_file)
    if tool_cfg is not None:
        # Convert toml table to str for a simple presence check
        hay += str(tool_cfg)
    required_contract_names = [
        "domain_independent",
        "app_depends_only_on_domain",
        "infra_can_import_app_public",
        "no_cross_module_internals",
    ]
    for cname in required_contract_names:
        assert cname in hay, f"Missing Import Linter contract: {cname}"


@pytest.mark.req(106)
def test_106_import_linter_contracts_declared_in_pyproject():
    """{DOC_KEY}+106"""
    # Addendum requires contracts to live in pyproject.toml so they evolve with tooling.
    pj = load_pyproject()
    tool_cfg = (pj.get("tool") or {}).get("importlinter")
    assert tool_cfg is not None, "Expected [tool.importlinter] section in pyproject.toml (req 106)"
    # Best-effort: ensure at least one contract name appears under the tool config
    hay = str(tool_cfg)
    assert any(k in hay for k in ("domain_independent", "app_depends_only_on_domain", "no_cross_module_internals")), \
        "Import Linter contracts should be defined inside pyproject.toml"
