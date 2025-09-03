# Testing Policy

## 🧠 Myth-busting

**1) Requirements live in one big document**  
_Myth:_ Requirements belong in a single, definitive specification.  
_Reality:_ In practice, requirements spread across tests, code, configuration, runtime behavior, and some prose. Forcing them into one document creates blind spots and slows adaptation.

**2) Duplication works fine if we keep things in sync**  
_Myth:_ Requirements can safely be repeated in different formats, as long as we maintain them.  
_Reality:_ Duplicates always drift apart. The safest approach is to define a single **source of truth** (commonly automated acceptance tests) and generate other views from it.

**3) Quality equals matching the requirements**  
_Myth:_ A product is “high quality” if it conforms to documented requirements.  
_Reality:_ Quality means **acceptance by users and stakeholders**. Passing automated acceptance tests proves fitness-for-purpose more reliably than matching documents.

**4) The code alone is sufficient**  
_Myth:_ Code fully expresses the system’s requirements.  
_Reality:_ Code shows _what_ the system does, but not _why_ or _for whom_. Automated tests capture expected outcomes, while lightweight architectural rules preserve long-term intent.

**5) More documents guarantee more quality**  
_Myth:_ The more documentation we write, the safer the system becomes.  
_Reality:_ Extra documents usually add more chances for drift. Small, **automated, enforceable artifacts** reduce risk far more effectively than volumes of prose.

**6) Natural language and code are interchangeable**  
_Myth:_ Any requirement can be expressed equally well in prose or executable code.  
_Reality:_ Only **measurable behavior** can be automated. Usability, intent, and non-functional needs require prose and collaboration to cover what executable checks cannot. Conversely, when behavior _is_ measurable, executable checks are the most reliable way to capture and enforce it.


**7) Prose is the best way to prove coverage**  
_Myth:_ Traceability documents are the most reliable way to show compliance.  
_Reality:_ **Machine-readable links** (tags, dashboards, coverage matrices) scale better and are easier to verify. Prose provides context, but compliance is stronger when tied to automation.



👉 **Bottom line:**  
Quality does not come from piles of documents. It comes from **automated, minimal, continuously validated checks**. Yet not all requirements are measurable. That’s why **tests enforce, prose explains, and collaboration aligns** — together keeping systems trustworthy and users satisfied.


* * *

## 📜 Policies



### 1. Correctness

* Tests run in CI.
    
* A change is valid only if its tests pass in CI.
    
* If something is not tested in CI, it is not verified.
    

### 2. CI

* The `main` branch is valid only when CI is green.
    
* Red CI blocks merges and releases.
    
* The last change affecting a failing area must investigate.
    

### 3. Flaky Tests

* A flaky test (passes and fails on the same code) must be quarantined with a tag and ticket.
    
* Quarantines expire after 7 days.
    
* Expired quarantines block merges until resolved.
    

### 4. Bugs

* A bug fix must include a test that would have detected the bug.
    
* That test must reference the bug ID.
    

### 5. Determinism

* Tests must be deterministic.
    
* Randomness must use fixed seeds.
    
* Clocks, networks, and fixtures must be controlled.
    
* External calls are allowed only in integration or end-to-end suites.
    

* * *

### 6. Mocking Strategy

**Goal:** fast, deterministic, focused unit tests by replacing external boundaries with mocks/fakes.

#### 6.1 Tools

* Prefer **pytest-mock** (`mocker` fixture) for patches/spies.
    
* `unittest.mock` is acceptable where convenient.
    

#### 6.2 What to mock

* **External libraries & I/O:** filesystem, network, environment, time, heavy parsers.
    
* **Process interactions:** `sys.exit`, `sys.argv`, `os.environ`.
    
* **Slow/nondeterministic code:** randomness, clocks, background threads.
    

#### 6.3 How to patch

* **Patch where used** (module under test), not where defined.
    
    * ✅ `mocker.patch("mug.cli.xmlschema.XMLSchema", ...)`
        
    * ❌ `mocker.patch("xmlschema.XMLSchema", ...)`
        
* Use `mocker.Mock()` / `mocker.spy()` to control behavior and assert calls.
    

#### 6.4 Unit vs Integration

* **Unit:** no real network, no large disk I/O; use mocks/fakes.
    
* **Integration/E2E:** real dependencies allowed; mark with `@pytest.mark.integration` (or similar).
    

#### 6.5 Logging & exit codes

* Use `caplog` to assert logs/levels.
    
* Use `pytest.raises(SystemExit)` or patch `sys.exit` to assert exit paths.
    

#### 6.6 Examples (illustrative)

```python
def test_validate_ok(mocker, capsys):
    fake_schema = mocker.Mock()
    fake_schema.iter_errors.return_value = []
    mocker.patch("mug.cli.xmlschema.XMLSchema", return_value=fake_schema)

    from mug.cli import _validate
    rc = _validate("doc.xml", "schema.xsd")
    assert rc == 0
    assert "OK" in capsys.readouterr().out
```

```python
def test_validate_schema_load_error(mocker, caplog):
    mocker.patch("mug.cli.xmlschema.XMLSchema", side_effect=Exception("boom"))
    from mug.cli import _validate
    rc = _validate("doc.xml", "bad.xsd")
    assert rc == 2
    assert "Failed to load schema" in caplog.text
```

```python
def test_validate_finds_errors(mocker):
    fake_schema = mocker.Mock()
    fake_schema.iter_errors.return_value = [Exception("line 4: invalid")]
    mocker.patch("mug.cli.xmlschema.XMLSchema", return_value=fake_schema)

    from mug.cli import _validate
    assert _validate("doc.xml", "schema.xsd") == 1
```

#### 6.7 Fixtures

* Put shared fixtures in `tests/conftest.py` (temp dirs, common mocks).
    
* Use `tmp_path` / `tmp_path_factory` for ephemeral files.
    

#### 6.8 Do / Don’t

* ✅ Force error paths by raising from mocked dependencies.
    
* ✅ Assert logs and exit codes.
    
* ❌ Depend on wall-clock time or the network in unit tests.
    
* ❌ Import heavy modules in `conftest` that slow collection.
    

* * *

### 7. Coverage Policy

**Goal:** prevent regressions with a hard coverage floor locally and in CI.

* **Local gate:** run with coverage and fail under the threshold.  
    _Recommended_: `pytest -q --cov=src --cov-report=term-missing --cov-fail-under=100`
    
* **CI gate:** the same floor is enforced in CI; PRs that reduce coverage fail.
    
* **Exceptions:** truly unreachable lines use `# pragma: no cover` with justification in review.
    

_Example (GitHub Actions):_

```yaml
- name: Test (pytest + coverage)
  run: |
    pytest -q --cov=src --cov-report=term-missing --cov-fail-under=100
- name: Coverage artifacts (optional)
  if: always()
  run: |
    pytest --cov=src --cov-report=html --cov-report=xml:coverage.xml --cov-fail-under=100
```

* * *

### 8. Smoke Tests

**Goal:** catch packaging/CLI regressions quickly with a tiny, fast suite.

* **Scope:** basic CLI availability and core commands:
    
    * `mug --version` prints SemVer string and exits 0.
        
    * `mug help` prints module commands.
        
    * `mug documents trace-id` prints UUIDv4 and exits 0.
        
    * `mug documents db build|info|drop|rebuild` succeed in sequence.
        
* **Location:** `tests/smoke/` (collected in CI).
    
* **Runtime:** < 10s total; no network; uses ephemeral temp dirs.
    

_Minimal pytest example:_

```python
import json, re, subprocess

def run(*args):
    cp = subprocess.run(["mug", *args], capture_output=True, text=True)
    return cp.returncode, cp.stdout.strip()

def test_version():
    rc, out = run("--version")
    assert rc == 0 and re.match(r"^\d+\.\d+\.\d+(?:[-+].+)?$", out)

def test_help_lists_documents():
    rc, out = run("help")
    assert rc == 0 and "documents: trace-id, add, db" in out

def test_trace_id():
    rc, out = run("documents", "trace-id")
    assert rc == 0 and re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", out)

def test_documents_db_lifecycle(tmp_path, monkeypatch):
    # Optional: point config to temp workspace if supported
    rc, _ = run("documents", "db", "build");    assert rc == 0
    rc, out = run("documents", "db", "info");   assert rc == 0 and json.loads(out)["meta"]["schema_version"] == "1"
    rc, _ = run("documents", "db", "drop");     assert rc == 0
    rc, _ = run("documents", "db", "rebuild");  assert rc == 0
```

* * *

### 9. Import Linter

**Goal:** enforce Clean Architecture and modular boundaries at import time.

* **Tool:** [`import-linter`](https://github.com/seddonym/import-linter?utm_source=chatgpt.com)
    
* **Policy:** encode contracts that reflect layers and modules. Adjust package names to your actual importable packages.
    

_Example `.importlinter` (tune to your package layout):_

```
[importlinter]
root_package = mug

[contract:ca-layering]
name = Clean Architecture layering
type = layers
layers =
    mug.common.domain
    mug.common.application
    mug.modules.system.domain
    mug.modules.system.application
    mug.modules.documents.application
    mug.modules.system.presentation
    mug.modules.documents.presentation
    mug.common.infrastructure
    mug.modules.system.infrastructure
    mug.modules.documents.infrastructure

[contract:modules-isolation]
name = Modules do not reach into each other’s internals
type = independence
modules =
    mug.modules.system
    mug.modules.documents
```

* **CI:** add a step that runs `lint-imports` (or `lint-imports --no-cache`) and fails on violation.
    

* * *

### 10. The `env-test` Branch

**Goal:** harden the app across environments without slowing `main` CI.

* **Branch:** `env-test` tracks `main` (rebased/merged regularly).
    
* **Matrix:** runs extended tests across OS / Python versions (e.g., `ubuntu-latest`, `macOS-latest`; Python `3.x` matrix).
    
* **Scope:** slow E2E, filesystem quirks, locale/timezone variance, large fixture sets, SQLite locking behavior.
    
* **Gating:**
    
    * `main` merges are blocked only by the standard CI gates (tests/coverage/import-linter).
        
    * **Releases** require a green `env-test` run within the last 48 hours (automation checks the latest workflow run).
        
* **Quarantine:** flaky tests in `env-test` follow the same 7-day quarantine policy.
    

_Example GH Actions sketch:_

```yaml
name: Env Test
on:
  push:
    branches: [env-test]
  schedule:
    - cron: "0 6 * * *"  # daily
jobs:
  matrix-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: ${{ matrix.python }} }
      - run: pip install -e ".[dev]"
      - run: pytest -q -m "integration or e2e" --maxfail=1
```

* * *

## 🔒 CI Enforcement Recap

* **Lint:** Ruff runs via repo `ruff.toml`; test paths excluded as configured.
    
* **Types:** mypy runs with agreed strictness.
    
* **Tests:** pytest executes unit & integration suites; markers honored.
    
* **Coverage Gate:** `--cov-fail-under=100` enforced locally and in CI.
    
* **Smoke Tests:** always on; must pass in CI.
    
* **Import Linter:** enforced in CI; fails on layer/module violations.
    
* **Env Test:** separate branch & nightly matrix; green within 48h required for release.
    

* * *