# tests/test_repo_guardrails.py

# Mypy plugin needs the path to the mypy.ini config file

"""
Automated guardrail tests generated from spec document_key=20250820T142442+0000.
Each test is tagged with @pytest.mark.req(<requirement_id>), and some tests
carry multiple IDs where the spec marks them as duplicates.

These tests use only stdlib + pytest. They statically inspect the repo
and CI workflow definitions to verify compliance. For CI runtime behaviors
that cannot be proven locally, we include stub tests with explanatory comments.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

import pytest

DOC_KEY = "20250820T142442+0000"  # traceability key from the XML spec

# ---- repo root detection (robust) --------------------------------------------
def _is_repo_root(p: Path) -> bool:
    return (p / "pyproject.toml").exists() or (p / ".git").exists()

def _discover_repo_root() -> Path:
    # 1) env override
    env = os.environ.get("MUG_REPO_ROOT")
    if env:
        pe = Path(env).resolve()
        if _is_repo_root(pe):
            return pe

    # 2) walk up from this file, then from CWD
    starts = [Path(__file__).resolve(), Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for cand in (start, *start.parents):
            if cand in seen:
                continue
            seen.add(cand)
            if _is_repo_root(cand):
                return cand

    # 3) last resort: the folder containing this file (debug-friendly)
    fallback = Path(__file__).resolve().parent
    print(
        "\n[repo-guardrails] WARNING: Could not auto-detect repo root.\n"
        f"Falling back to: {fallback}\n"
        "Tip: set MUG_REPO_ROOT=C:\\path\\to\\repo\n"
    )
    return fallback

REPO_ROOT = _discover_repo_root()
SRC_DIR = REPO_ROOT / "src"
DOCS_DIR = REPO_ROOT / "docs"
GITHUB_WF = REPO_ROOT / ".github" / "workflows"



# ---- helpers -----------------------------------------------------------------

def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def find_workflow_files() -> list[Path]:
    if not GITHUB_WF.exists():
        return []
    return [p for p in GITHUB_WF.iterdir() if p.suffix in {".yml", ".yaml"} and p.is_file()]

def workflow_texts() -> list[str]:
    return [load_text(p) for p in find_workflow_files()]

def has_any_workflow_matching(patterns: Iterable[str]) -> bool:
    texts = workflow_texts()
    if not texts:
        return False
    for t in texts:
        if all(re.search(p, t, flags=re.IGNORECASE | re.MULTILINE) for p in patterns):
            return True
    return False

def any_workflow_has(pattern: str) -> bool:
    return any(re.search(pattern, t, flags=re.IGNORECASE | re.MULTILINE) for t in workflow_texts())

def in_any_file(globs: Iterable[str], pattern: str) -> bool:
    rx = re.compile(pattern, re.IGNORECASE)
    for g in globs:
        for p in REPO_ROOT.glob(g):
            if p.is_file() and rx.search(load_text(p)):
                return True
    return False

def first_top_pkg() -> Optional[str]:
    """Return the first top-level package name under src/ that looks importable."""
    if not SRC_DIR.exists():
        return None
    for child in sorted(SRC_DIR.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists():
            return child.name
    return None

def has_any(path_candidates: Iterable[Path]) -> bool:
    return any(p.exists() for p in path_candidates)

def load_pyproject() -> dict:
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    # Python 3.11+ has tomllib; fall back to simple regex if unavailable.
    try:
        import tomllib  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        load_text(pyproject)
        # Super-lightweight parse: find [tool.ruff] etc. if needed by regex consumers below.
        # For fields, we truly need (project.scripts, tool.setuptools.*), we try tomllib first.
        raise AssertionError("Python 3.11+ (with tomllib) required to parse pyproject.toml")
    with pyproject.open("rb") as f:
        return tomllib.load(f)

def json_load_if_exists(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    return json.loads(load_text(path))

# ---- 1. Project Skeleton & Core Files ---------------------------------------

@pytest.mark.req(1)
def test_req_1_pyproject_exists_and_parses():
    """{DOC_KEY}+1"""
    _ = load_pyproject()  # asserts file exists & parses

@pytest.mark.req(2)
def test_req_2_readme_exists():
    """{DOC_KEY}+2"""
    assert (REPO_ROOT / "README.md").exists()

@pytest.mark.req(3)
def test_req_3_license_exists():
    """{DOC_KEY}+3"""
    assert (REPO_ROOT / "LICENSE").exists()

@pytest.mark.req(4)
def test_req_4_gitignore_exists():
    """{DOC_KEY}+4"""
    assert (REPO_ROOT / ".gitignore").exists()

@pytest.mark.req(5)
def test_req_5_docs_dir_exists():
    """{DOC_KEY}+5"""
    assert DOCS_DIR.exists() and DOCS_DIR.is_dir()

import pytest

@pytest.mark.req(37)
def test_req_37_testing_policy_exists():
    """{DOC_KEY}+37"""
    path = DOCS_DIR / "TESTING_POLICY.md"
    assert path.exists(), "docs/TESTING_POLICY.md must exist"


@pytest.mark.req(38)
def test_req_38_contributing_exists_and_mentions_workflow():
    """{DOC_KEY}+38"""
    path = DOCS_DIR / "CONTRIBUTING.md"
    assert path.exists(), "docs/CONTRIBUTING.md must exist"
    txt = load_text(path)
    # Look for local steps + PR/branch + commit conventions
    for pat in [r"(lint|ruff|mypy|pytest)", r"\bPR\b|\bpull request\b", r"(conventional|commitlint)"]:
        assert re.search(pat, txt, re.IGNORECASE), f"Missing expected mention: {pat}"

@pytest.mark.req(39)
def test_req_39_docs_changelog_exists():
    """{DOC_KEY}+39"""
    assert (DOCS_DIR / "CHANGELOG.md").exists()

# ---- 2. Configuration & Tooling ---------------------------------------------

@pytest.mark.req(6)
def test_req_6_ruff_config_present():
    """{DOC_KEY}+6"""
    py = REPO_ROOT / "pyproject.toml"
    txt = load_text(py) if py.exists() else ""
    ruff_toml = REPO_ROOT / "ruff.toml"
    assert ruff_toml.exists() or re.search(r"\[tool\.ruff]", txt), "Need ruff.toml or [tool.ruff] in pyproject"

@pytest.mark.req(7)
def test_req_7_mypy_ini_present():
    """{DOC_KEY}+7"""
    assert (REPO_ROOT / "mypy.ini").exists()

@pytest.mark.req(8)
def test_req_8_pytest_ini_present():
    """{DOC_KEY}+8"""
    ini = REPO_ROOT / "pytest.ini"
    assert ini.exists(), "pytest.ini required"
    assert "pytest" in load_text(ini).lower()

# ---- 3. Packaging & Importability -------------------------------------------

@pytest.mark.req(9)
def test_req_9_top_package_init_exists():
    """{DOC_KEY}+9"""
    assert first_top_pkg() is not None, "No top-level package with __init__.py under src/"

@pytest.mark.req(10)
def test_req_10_py_typed_exists():
    """{DOC_KEY}+10"""
    pkg = first_top_pkg()
    assert pkg, "No package found"
    assert (SRC_DIR / pkg / "py.typed").exists()

@pytest.mark.req(11)
def test_req_11_import_package_succeeds():
    """{DOC_KEY}+11"""
    pkg = first_top_pkg()
    assert pkg, "No package found"
    sys.path.insert(0, str(SRC_DIR))
    try:
        importlib.invalidate_caches()
        importlib.import_module(pkg)
    finally:
        sys.path.pop(0)

@pytest.mark.req(12)
def test_req_12_project_scripts_defined():
    """{DOC_KEY}+12"""
    pj = load_pyproject()
    scripts = pj.get("project", {}).get("scripts", {})
    assert isinstance(scripts, dict) and len(scripts) >= 1, "Expect ≥1 console script in [project.scripts]"

@pytest.mark.req(13)
def test_req_13_no_root_requirements_or_setup():
    """{DOC_KEY}+13"""
    assert not (REPO_ROOT / "requirements.txt").exists(), "Root requirements.txt should not exist"
    assert not (REPO_ROOT / "setup.py").exists(), "Root setup.py should not exist"

import re
from pathlib import Path

@pytest.mark.req(33)
def test_req_33_manifest_in_policy():
    """{DOC_KEY}+33"""
    mf = REPO_ROOT / "MANIFEST.in"
    assert mf.exists(), "MANIFEST.in required"

    txt = load_text(mf)

    def assert_has_any(patterns, msg):
        for pat in patterns:
            if re.search(pat, txt, re.IGNORECASE):
                return
        raise AssertionError(msg + f" (looked for any of: {patterns})")

    # --- Always-required metadata files ---
    required = [
        r"include\s+pyproject\.toml",
        r"include\s+README\.md",
        r"include\s+LICENSE",
    ]
    for pat in required:
        assert re.search(pat, txt, re.IGNORECASE), f"MANIFEST.in missing: {pat}"

    # --- Ensure source is included via any reasonable pattern ---
    assert_has_any(
        [
            r"recursive-include\s+src\s+\*\.py",
            r"graft\s+src",
            r"include\s+src/.*\*\.py",  # permissive variant
        ],
        "MANIFEST.in should include Python sources under src/",
    )

    # --- Conditionally require stubs/typed markers if present in the repo ---
    has_pyi = any(REPO_ROOT.glob("src/**/*.pyi"))
    if has_pyi:
        assert re.search(r"recursive-include\s+src\s+.*\.pyi", txt, re.IGNORECASE), \
            "Include .pyi stubs when they exist (e.g., 'recursive-include src *.pyi')"

    # If any top-level package contains a py.typed file, require it to be declared
    has_py_typed = any(p.exists() for p in REPO_ROOT.glob("src/**/py.typed"))
    if has_py_typed:
        assert re.search(r"recursive-include\s+src\s+py\.typed", txt, re.IGNORECASE), \
            "Include py.typed markers when present (PEP 561)"

    # --- Hygiene: allow common variants for excluding bytecode ---
    assert_has_any(
        [
            r"global-exclude\s+\*\.pyc",
            r"global-exclude\s+\*\.py[cod]",
        ],
        "Add a global-exclude for Python bytecode files",
    )

    # --- Optional: do not over-constrain pruning; accept any of these if present ---
    # This keeps the policy flexible while still encouraging lean sdists.
    optional_prunes = [
        r"prune\s+\.github",
        r"prune\s+\.husky",
        r"prune\s+scripts",
        r"prune\s+tests",
        r"prune\s+docs",
    ]
    # Not required, but if you choose to prune, ensure the syntax is valid.
    for pat in optional_prunes:
        _ = re.search(pat, txt, re.IGNORECASE)  # no assert

@pytest.mark.req(34)
def test_req_34_setuptools_parity_config():
    """{DOC_KEY}+34"""
    pj = load_pyproject()
    tool = pj.get("tool", {})
    st = tool.get("setuptools", {})
    assert st.get("include-package-data") is True, "include-package-data = true required"
    pkg_data = st.get("package-data", {})
    # Accept any package key mapping to ["py.typed"]
    assert any(v == ["py.typed"] for v in pkg_data.values()), "package-data must map to ['py.typed']"

@pytest.mark.req(35)
def test_req_35_sdist_contains_essentials_stub():
    """{DOC_KEY}+35"""
    # This requires building a sdist and inspecting its contents in CI.
    # id=35 cannot be fully validated locally without running the build.
    # See id=36/68-70 for CI packaging smoke tests that cover this in pipelines.
    # STUB per instructions:
    # id cannot be tested with an automated test (without running the build).
    assert True

# ---- 4. Structure & Hygiene --------------------------------------------------

@pytest.mark.req(15)
def test_req_15_all_pkg_dirs_have_init():
    """{DOC_KEY}+15"""
    pkg = first_top_pkg()
    assert pkg, "No package found"
    for dirpath, dirnames, filenames in os.walk(SRC_DIR / pkg):
        dp = Path(dirpath)
        if any(f.endswith(".py") for f in filenames):
            assert (dp / "__init__.py").exists(), f"Missing __init__.py in {dp}"

@pytest.mark.req(16)
def test_req_16_no_wildcard_imports():
    """{DOC_KEY}+16"""
    assert not in_any_file(["src/**/*.py"], r"from\s+\S+\s+import\s+\*"), "Wildcard imports found"

@pytest.mark.req(17)
def test_req_17_no_sys_path_mutation():
    """{DOC_KEY}+17"""
    bad = r"sys\.path\.(append|insert|extend)\s*\("
    assert not in_any_file(["src/**/*.py"], bad), "Detected sys.path mutation in package code"

# ---- 5. Commit Hygiene & Versioning -----------------------------------------

@pytest.mark.req(18, 40)
def test_commitlint_config_present():
    """{DOC_KEY}+18,40"""
    assert (REPO_ROOT / "config" / "node" / "commitlint.config.js").exists()

@pytest.mark.req(19, 41)
def test_husky_commit_msg_hook_present():
    """{DOC_KEY}+19,41"""
    assert (REPO_ROOT / ".husky" / "commit-msg").exists()

@pytest.mark.req(20, 42, 55)
def test_ci_runs_commitlint_on_push_and_pr():
    """{DOC_KEY}+20,42,55"""
    assert has_any_workflow_matching([
        r"on:\s*(?:\[\s*(?:push\s*,\s*pull_request|pull_request\s*,\s*push)\s*\]|(?:\n\s*)?(?:push:|pull_request:))",
        r"commitlint"
    ])

@pytest.mark.req(21, 43)
def test_conventional_changelog_config_present():
    """{DOC_KEY}+21,43"""
    assert (REPO_ROOT / "config" / "node" / "conventional-changelogrc.js").exists()

@pytest.mark.req(22, 44, 45)
def test_package_json_has_changelog_script_and_changelog_md():
    """{DOC_KEY}+22,44,45"""
    pj = json_load_if_exists(REPO_ROOT / "package.json")
    assert pj and isinstance(pj, dict), "package.json must exist"
    scripts = pj.get("scripts", {})
    assert "changelog" in scripts, "package.json must define a 'changelog' script"
    assert (REPO_ROOT / "docs" / "CHANGELOG.md").exists(), "CHANGELOG.md must be tracked"

# ---- 6. CI / Automation ------------------------------------------------------

@pytest.mark.req(23, 49, 50, 51)
def test_pr_checks_workflow_runs_ruff_mypy_pytest():
    """{DOC_KEY}+23,49,50,51"""
    assert has_any_workflow_matching([r"pull_request", r"(ruff|python -m ruff)"])
    assert has_any_workflow_matching([r"pull_request", r"\bmypy\b"])
    assert has_any_workflow_matching([r"pull_request", r"\bpytest\b"])

@pytest.mark.req(24, 59)
def test_ci_cd_workflow_triggers_on_main_and_tags():
    """{DOC_KEY}+24,59"""


  # One workflow file must contain:
  # - a push trigger (mapping form)
  # - a branches filter for main (accepts [ main ], - main, or main; quoted or unquoted)
  # - a tags filter matching v*.*.* (list or dash; quoted or unquoted)

    assert has_any_workflow_matching([
        r"on:\s*(push:)|on:\s*\n\s*push:",
        r"(branches:\s*\[\s*'?main'?\s*\]|branches:\s*-\s*'?main'?|branches:\s*'?main'?)",
        r"tags:\s*(?:\[\s*'?(?:v\*\.?\*\.?\*)'?\s*\]|(?:\n\s*-\s*'?(?:v\*\.?\*\.?\*)'?\s*))"
    ])

@pytest.mark.req(25)
def test_req_25_has_pyproject_or_workflows():
    """{DOC_KEY}+25"""
    assert (REPO_ROOT / "pyproject.toml").exists() or GITHUB_WF.exists()

import re
import pytest


@pytest.mark.req(36, 68)
def test_ci_builds_wheel_and_sdist():
    pattern = r"python\s+-m\s+build(?=[\s\S]*--sdist)(?=[\s\S]*--wheel)"
    assert any_workflow_has(pattern), "Expected `python -m build` to produce both sdist and wheel."


# --- Install (Req 36, 69) ---
@pytest.mark.req(36, 69)
def test_ci_installs_from_local_dist_offline():
    pattern = (
        r"(?:pip|python\s+-m\s+pip)\s+install"
        r"(?=[\s\S]*--no-index)"
        r"(?=[\s\S]*(?:--find-links\s*=\s*dist|dist/[^ \n]+\.whl))"
        r"[\s\S]*\.whl"
    )
    assert any_workflow_has(pattern), "Expected offline install from dist/ (with --no-index and dist as source)."



# --- Import + print version (Req 36, 70) ---
@pytest.mark.req(36, 70)
def test_ci_smoke_import_and_prints_version():
    pattern = (
        r"python\s+-c\s+[\"']\s*import\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;"
        r"\s*print\(\s*\1\.__version__\s*\)\s*[\"']"
    )
    assert any_workflow_has(pattern), "Expected `python -c` to import the package and print <pkg>.__version__."

# ---- 7. Cross-Project Scripts ------------------------------------------------

@pytest.mark.req(26)
def test_req_26_scripts_folder_exists():
    """{DOC_KEY}+26"""
    assert (REPO_ROOT / "scripts").exists()

@pytest.mark.req(27)
def test_req_27_packaging_helper_present():
    """{DOC_KEY}+27"""
    assert has_any([(REPO_ROOT / "scripts" / "package_helper" / "package.sh"),
                    (REPO_ROOT / "scripts" / "package_helper" / "package.ps1")])

# ---- 8. Logging & Error Handling --------------------------------------------

@pytest.mark.req(28)
def test_req_28_logging_has_console_and_file_handlers():
    """{DOC_KEY}+28"""
    has_stream = in_any_file(["src/**/*.py"], r"logging\.StreamHandler\s*\(")
    has_rotating = in_any_file(["src/**/*.py"], r"(RotatingFileHandler|TimedRotatingFileHandler)\s*\(")
    assert has_stream and has_rotating, "Expect both console and file handlers configured"

@pytest.mark.req(29)
def test_req_29_global_error_handler_installed():
    """{DOC_KEY}+29"""
    assert in_any_file(["src/**/*.py"], r"sys\.excepthook\s*="), "Global sys.excepthook not found"

# ---- 9. Testing Practices ----------------------------------------------------

@pytest.mark.req(30)
def test_req_30_coverage_enabled_and_configured():
    """{DOC_KEY}+30"""
    coveragerc = (REPO_ROOT / ".coveragerc").exists()
    has_cov_cli = in_any_file(
        ["pytest.ini", "pyproject.toml"],
        r"--cov(=|\s)"
    )
    assert coveragerc and has_cov_cli, "Expect .coveragerc and pytest opts enabling coverage"

@pytest.mark.req(31)
def test_req_31_conftest_exists_for_fixtures():
    """{DOC_KEY}+31"""
    assert (REPO_ROOT / "tests" / "conftest.py").exists()

@pytest.mark.req(32)
def test_req_32_mocking_strategy_available_or_documented():
    """{DOC_KEY}+32"""
    # Either declare pytest-mock in deps OR document mocking in TESTING_POLICY.md
    documented = (DOCS_DIR / "TESTING_POLICY.md").exists() and re.search(
        r"(pytest-mock|mock)", load_text(DOCS_DIR / "TESTING_POLICY.md"), re.IGNORECASE
    )
    # Quick dependency scan in pyproject:
    deps_ok = False
    try:
        pj = load_pyproject()
        deps = (pj.get("project", {}).get("dependencies") or []) + (pj.get("project", {}).get("optional-dependencies", {}).get("dev", []) or [])
        deps_ok = any("pytest-mock" in d for d in deps)
    except AssertionError:
        pass
    assert documented or deps_ok, "Need mocking plugin in deps or documented strategy"

# Section 1.12 — CLI & Entry Points

@pytest.mark.req(71)
def test_req_71_mug_console_script_present():
    """{DOC_KEY}+71"""
    pj = load_pyproject()
    scripts = pj.get("project", {}).get("scripts", {})
    assert "mug" in scripts, "[project.scripts] must define a 'mug' console script"
    assert scripts["mug"] == "mug.cli:main", "'mug' must map to 'mug.cli:main'"


@pytest.mark.req(72)
def test_req_72_mug_validate_alias_optional_but_correct_if_present():
    """{DOC_KEY}+72"""
    pj = load_pyproject()
    scripts = pj.get("project", {}).get("scripts", {})
    alias = scripts.get("mug-validate")
    # Optional: if present, it must invoke the same validator entry point as 'mug'
    if alias is not None:
        assert alias in {"mug.cli:main", "mug.cli:cli_validate"}, (
            "If 'mug-validate' is provided, it must point to 'mug.cli:main' or 'mug.cli:cli_validate'"
        )
    else:
        # alias not required — pass
        assert True


@pytest.mark.req(73)
def test_req_73_module_dunder_main_exists_for_python_dash_m():
    """{DOC_KEY}+73"""
    # Requirement text refers specifically to 'python -m mug', so assert src/mug/__main__.py exists.
    assert (REPO_ROOT / "src" / "mug" / "__main__.py").exists(), "Expect src/mug/__main__.py so 'python -m mug' works"


@pytest.mark.req(74)
def test_req_74_docs_show_supported_invocations_and_forbid_python_dash_m_mug_validate():
    """{DOC_KEY}+74"""
    # Look for at least one doc mentioning 'mug ...' or 'python -m mug ...'
    ok = in_any_file(
        ["README.*", "docs/**/*.md", "docs/**/*.rst"],
        r"\b(mug\s+\S+|python\s+-m\s+mug\b)"
    )
    # And ensure docs do NOT recommend `python -m mug-validate` (hyphens invalid in module paths)
    forbid = in_any_file(
        ["README.*", "docs/**/*.md", "docs/**/*.rst"],
        r"\bpython\s+-m\s+mug-validate\b"
    )
    assert ok, "Docs must show how to run either 'mug …' or 'python -m mug …'"
    assert not forbid, "Docs must NOT suggest 'python -m mug-validate' (hyphens invalid in module names)"


@pytest.mark.req(75)
def test_req_75_docs_indicate_install_before_using_console_scripts():
    """{DOC_KEY}+75"""
    # Lightweight automation for a manual requirement:
    # Verify docs mention installing before using console scripts (pip/pipx install).
    has_install_hint = in_any_file(
        ["README.*", "docs/**/*.md", "docs/**/*.rst"],
        r"\b(pipx?\s+install|pip\s+install\s+-e\s+\.)\b"
    )
    assert has_install_hint, "Docs should indicate installing the package before using console scripts (e.g., 'pip install -e .')"


@pytest.mark.req(76)
def test_req_76_script_targets_have_no_hyphens_in_module_path():
    """{DOC_KEY}+76"""
    pj = load_pyproject()
    scripts = pj.get("project", {}).get("scripts", {})
    # Each console script target is of the form "module.path:callable".
    # The module path (left of ':') must not contain hyphens.
    bad = []
    for name, target in scripts.items():
        if not isinstance(target, str) or ":" not in target:
            bad.append((name, target, "Target must be a 'module.path:callable' string"))
            continue
        module_path, _, callable_name = target.partition(":")
        if "-" in module_path:
            bad.append((name, target, "Module path must not contain hyphens"))
        if not module_path or not callable_name:
            bad.append((name, target, "Both module path and callable must be non-empty"))
    assert not bad, "Invalid console script targets:\n" + "\n".join(f"- {n}: {t} → {why}" for n, t, why in bad)

