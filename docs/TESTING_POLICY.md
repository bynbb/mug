# 🧪 Testing Policy

## 1. Correctness

* Tests must run in CI.
* A change is valid only if its tests pass in CI.
* If something is not tested in CI, it is not verified.

## 2. CI

* The main branch is valid only when CI is green.
* Red CI blocks merges and releases.
* The last change affecting a failing area must investigate.

## 3. Flaky Tests

* A flaky test (one that passes and fails on the same code) must be quarantined with a tag and ticket.
* Quarantines expire after 7 days.
* Expired quarantines block merges until resolved.

## 4. Bugs

* A bug fix must include a test that would have detected the bug.
* That test must reference the bug ID.

## 5. Determinism

* Tests must be deterministic.
* Randomness must use fixed seeds.
* Clocks, networks, and fixtures must be controlled.
* External calls are allowed only in integration or end-to-end suites.

---

## 6. Mocking Strategy

**Goal:** make unit tests fast, deterministic, and focused by replacing external boundaries with mocks/fakes.

### 6.1 Tools

* Prefer **pytest-mock** (`mocker` fixture) for patches and spies.
* Built-in `unittest.mock` is acceptable where convenient.

### 6.2 What to mock

* **External libraries & I/O:** e.g., `xmlschema.XMLSchema`, `iter_errors`, filesystem reads/writes, network, environment, time.
* **Process interactions:** `sys.exit`, `sys.argv`, `os.environ`.
* **Slow or nondeterministic code:** random, clocks, background threads.

### 6.3 How to patch

* **Patch where used** (module under test), not where defined:

  * ✅ `mocker.patch("mug.cli.xmlschema.XMLSchema", ...)`
  * ❌ `mocker.patch("xmlschema.XMLSchema", ...)` (won’t affect already-imported symbols)
* Use `mocker.Mock()` / `mocker.spy()` to control behavior and assert calls.

### 6.4 Unit vs Integration

* **Unit tests:** no real network, no large disk I/O; use mocks/fakes.
* **Integration/E2E:** allowed to touch real dependencies; mark with `@pytest.mark.integration` (or similar).

### 6.5 Logging & exit codes

* Use `caplog` to assert log messages/levels.
* Use `pytest.raises(SystemExit)` or patch `sys.exit` to assert exit paths.

### 6.6 Examples (illustrative)

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

### 6.7 Fixtures

* Put shared fixtures in `tests/conftest.py` (e.g., `repo_root`, temp dirs, common mocks).
* Use `tmp_path`/`tmp_path_factory` for ephemeral files.

### 6.8 Do / Don’t

* ✅ Do force error paths by raising from mocked dependencies.
* ✅ Do assert logs and exit codes.
* ❌ Don’t depend on wall-clock time or network in unit tests.
* ❌ Don’t import heavy modules in `conftest` that slow collection.

---


## 7. Coverage Policy

**Goal:** prevent regressions by enforcing a hard coverage floor in local runs and CI.

* **Local gate:** run tests with coverage and fail if below threshold.

  * Recommended: `pytest -q --cov=src --cov-report=term-missing --cov-fail-under=100`.
* **CI gate:** the coverage floor is enforced in CI; PRs that reduce coverage fail the build.

  * Example (GitHub Actions):

    ```yaml
    - name: Test (pytest + coverage)
      run: |
        pytest -q --cov=src --cov-report=term-missing --cov-fail-under=100
    - name: Coverage artifacts (optional)
      if: always()
      run: |
        pytest --cov=src --cov-report=html --cov-report=xml:coverage.xml --cov-fail-under=100
    ```
* **Exceptions:** if a line is truly unreachable by design, annotate with `# pragma: no cover` and justify in code review.

---

## 8. Smoke Tests

TODO

## 9. Import Linter

TODO

## 10. The `env-test` Branch

TODO

---

## CI Enforcement Recap


* **Lint:** Ruff runs with repo‑root `ruff.toml`; tests exclude paths as configured.
* **Types:** mypy runs in CI with strictness appropriate for the codebase.
* **Tests:** pytest executes unit & integration suites; requirement markers are honored.
* **Coverage Gate:** CI fails if `--cov-fail-under` is breached; HTML/XML reports are archived as artifacts.
* **Smoke Test:** TODO
* **Import Linter:** TODO
* **The `env-test` Branch:** TODO



