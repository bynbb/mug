# Contributing

This project uses the **Conventional Commits** standard for all commit messages.  
Commit message format is enforced by Commitlint and Husky.

**Examples:**

* `feat: add new CLI command`
    
* `fix: handle edge case in argument parsing`
    
* `chore: update dependencies`
    

Refer to the Conventional Commits documentation for full details.

* * *

## Local Setup

1. Run `npm install` in the `devtools/` folder to install `@commitlint/cli`, `@commitlint/config-conventional`, and `husky`.
    
2. Run `npm run prepare` to set up Husky Git hooks.
    

After setup, **all commits are automatically checked for proper Conventional Commits format.**  
Release notes and the `CHANGELOG.md` file are updated by [Release Drafter](https://github.com/release-drafter/release-drafter) when pull requests are merged to `main`.

* * *

## Code Linting and Formatting

To ensure a consistent codebase, **run linting and formatting before committing your changes**:

1. **Install Python tooling (if not already installed):**
    
    ```bash
    pip install ruff black
    ```
    
2. **Lint the code:**
    
    ```bash
    ruff .
    ```
    
    Fix any issues reported.
    
3. **Format the code:**
    
    ```bash
    black .
    ```
    
4. Ensure both tools report zero issues or warnings before committing.
    

* * *

## Running Tests

* Make sure all tests pass before opening a pull request:
    
    ```bash
    pytest
    ```
    

* * *

## Checklist (Before You Commit)

*  Code is linted (`ruff`) and formatted (`black`)
    
*  All tests pass (`pytest`)
    
*  Commit message follows Conventional Commits standard
    

* * *