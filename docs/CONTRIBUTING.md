# Contributing

⚠️ **Pre-1.0.0 Policy**: _History may change at any time._  
Anything goes before `v1.0.0`. Consumers should not depend on stability until we release `v1.0.0`.

* * *

## Branch and Versioning Policy

We follow Semantic Versioning with one maxim:

**Anything goes before v1.0.0.**

* **`env-test` branch**
    
    * Permanent sandbox for CI/CD experimentation.
        
    * Always versioned as `0.0.Z`.
        
    * Force pushes and history rewrites are acceptable.
        
    * Never tagged beyond `0.0.*`.
        
    * Not for external consumption.
        
* **`main` branch**
    
    * Primary branch for app development.
        
    * Iterates as `0.Y.0` until `v1.0.0`.
        
    * History may be rewritten until `v1.0.0`.
        
    * Once `v1.0.0` is cut:
        
        * History becomes stable.
            
        * Tags become immutable contracts.
            
        * Force pushes are no longer allowed.
            

* * *

## Commit Messages

This project uses the **Conventional Commits** standard.  
Commit messages are enforced by Commitlint and Husky.

**Examples:**

* `feat: add new CLI command`
    
* `fix: handle edge case in argument parsing`
    
* `chore: update dependencies`
    

Refer to Conventional Commits for full details.

* * *

## Local Setup

1. Run `npm install` in the `devtools/` folder to install `@commitlint/cli`, `@commitlint/config-conventional`, and `husky`.
    
2. Run `npm run prepare` to set up Husky Git hooks.
    

After setup, all commits are automatically checked for proper format.  
Release notes and `CHANGELOG.md` are updated by [Release Drafter](https://github.com/release-drafter/release-drafter?utm_source=chatgpt.com) when pull requests are merged to `main`.

* * *

## Code Linting

To ensure a consistent codebase, run linting before committing:

1. Install Python tooling:
    
    ```bash
    pip install ruff
    ```
    
2. Lint the code:
    
    ```bash
    ruff .
    ```
    
3. Fix any issues until `ruff` reports zero problems.
    

* * *

## Running Tests

All contributions must keep the test suite green:

```bash
pytest
```

* CI will run tests automatically on both `main` and `env-test`.
    
* Coverage thresholds are enforced via `pytest.ini`.
    

* * *

## Checklist (Before You Commit)

* Code is linted (`ruff`)
    
* All tests pass (`pytest`)
    
* Commit message follows Conventional Commits
    
* You understand the **branch/versioning policy** and that **pre-1.0.0 history is fluid**
    

* * *