# mug — env-test

This branch is a permanent environment-smoke sandbox.
Goal: prove Windows/amd64 (Docker) → ARM64 runner (Actions) with minimal tests.

- Requirements test lives in `tests/env/` and fails until both arches pass.
- Granular tests write `.smoke/build-results.json`.
- 

- Test push
