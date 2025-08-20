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

## 6. Traceability

* Each test must link to a `document_key + requirement_id`.
* Requirement IDs must remain stable within a document.
