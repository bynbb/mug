# What matches the guide (✅)

* **Single composition area present**: `src/mug/composition/{__main__.py, bootstrap.py}` exists and owns startup (no DI leakage).
    
* **Modules-as-services scaffolding**: `src/mug/modules/users/{composition,domain,application,infrastructure,presentation}` are in place.
    
* **Common layer**: `mug/common/*` exists; the **Mediator is async-ready** (`async def send(...)` with `inspect.isawaitable`), matching the addendum.
    
* **Entry point**: `[project.scripts].mug = "mug.composition.__main__:main"`.
    

# What diverges from the guide (🚧) — with concrete fixes

1. **PEP 420 namespaces (critical)**
    

* **Current**: `__init__.py` exists at `src/mug/` and at _every_ layer root under modules (e.g., `modules/users/{domain,application,...}/__init__.py`).
    
* **Guide**: No `__init__.py` at `src/mug` nor at layer roots—namespace packages should be implicit.
    
* **Fix**: Delete these files:
    
    * `src/mug/__init__.py`
        
    * `src/mug/modules/__init__.py`
        
    * `src/mug/modules/users/__init__.py`
        
    * `src/mug/modules/users/{domain,application,infrastructure,presentation,composition}/__init__.py`
        
* **Packaging note**: You’re using **Hatch** (`hatchling`), whereas the guide shows **setuptools**. That’s okay—just ensure packaging still includes the namespace tree. Your `tool.hatch.build.targets.wheel.packages = ["src/mug"]` will pick up `mug` even without `__init__.py`. If you later move to setuptools, use `packages.find` with `namespaces = true`.
    

2. **Import Linter contracts missing**
    

* **Current**: No `[tool.importlinter]` in `pyproject.toml`.
    
* **Guide**: Contracts enforce boundaries (no cross-module imports, no one imports composition, CA layers).
    
* **Fix**: Add the contracts from the guide into `pyproject.toml` and wire them in CI. (If you keep Hatch, the contracts are still just a `[tool.importlinter]` table—totally compatible.)
    

3. **Composition should mount module CLIs + register handlers**
    

* **Current**: `composition/__main__.py` creates a `Typer()` and calls `bootstrap()`, but does **not** mount any module Typer apps nor pass the mediator’s `send`. `modules/users/presentation/public.py` defines a `Typer` app but nothing is wired into root.
    
* **Guide**: Root CLI composes sub-apps and passes `send` into presentation.
    
* **Fix (minimal)**:
    
    * In `bootstrap.py`, return both the mediator **and** perform handler registration (or provide a container and register there).
        
    * In `__main__.py`, mount the users CLI:
        
        ```python
        import typer
        from .bootstrap import bootstrap
        from mug.modules.users.presentation.public import app as users_app
        
        app = typer.Typer(help="Mug CLI", no_args_is_help=True)
        
        def main() -> int:
            mediator = bootstrap()
            # If your users CLI needs send, expose it in presentation and pass mediator.send
            app.add_typer(users_app, name="users")
            app()  # run Typer
            return 0
        ```
        
    * Evolve `users.presentation.public` to accept an injected `send` (as in the guide’s `get_app(send)` pattern) once you add commands.
        

4. **Dependency-Injector not used (by design choice)**
    

* **Current**: No `dependency-injector` usage anywhere. (Dependency declared but unused.)
    
* **Guide**: DI framework is confined to **composition**; modules stay DI-agnostic.
    
* **Fix (optional but recommended)**: Add a small container in `composition/` and register handlers there, then inject `send` into presentation. This becomes important as soon as infra adapters (DB/HTTP) appear.
    

5. **Module content is skeletal (CQRS/Mediator paths)**
    

* **Current**: No commands/queries/handlers in `users.application`; infra is empty; `presentation` has only a bare `Typer()` with no commands.
    
* **Guide**: Presentation sends **commands/queries**; application holds **handlers**; infra implements **ports**.
    
* **Fix**: Add one end-to-end example (like the guide’s `users.create` / `users.show`) to validate wiring, and a `system.version` path that reads version via infra (instead of doing versioning in `mug/__init__.py`).
    

6. **Argparse side-car (`mug/cli.py`)**
    

* **Current**: A separate `argparse` CLI exists and uses `xmlschema`. It’s not connected to the Typer root.
    
* **Guide**: CLI lives under presentation slices and is **Typer/Click-based**.
    
* **Fix**: Either migrate those commands into a module’s `presentation` (preferred), or keep `cli.py` as a _separate_ tool (not part of `mug` entrypoint). Avoid mixing two CLIs for the same package.
    

7. **Tooling parity**
    

* **Current**: No coverage config, no import-linter config, no explicit exit policy mapping; tests exist.
    
* **Guide**: Coverage + contracts + exit mapping; error taxonomy.
    
* **Fix (quick)**:
    
    * Add `[tool.coverage.*]` (from the guide) and run in CI.
        
    * Introduce `DomainError/ValidationError/NotFound/...` (you already have a base `DomainError` in `common.domain.public`), and centralize exit codes in composition.
        
    * Add a no-op telemetry hook in `bootstrap()` (you already left a placeholder).
        

# Boundary checks from the code (automated scan)

* **No DI found outside composition** ✅
    
* **No service-locator patterns** (`container.get(...)`, `providers.*`) ✅
    
* **No cross-module imports** (`mug.modules.X` importing `mug.modules.Y`) ✅
    
* **No domain-layer I/O detected** (heuristic scan) ✅
    
* **Composition importing domain** ❌ Not observed (good).
    
* **Presentation importing domain/infra** ❌ Not observed (good).
    

# Packaging & metadata

* **Build system**: Hatchling (`hatchling.build`) vs. guide’s setuptools—both fine.
    
* **Script entry**: correct.
    
* **Versioning**: currently in `mug/__init__.py`; move “show version” to a `system` module use case to align with the pattern.
    

# Priority checklist (do these first)

1. **Remove `__init__.py` at namespace roots and layer roots** (PEP 420).
    
2. **Mount module CLIs in root Typer app** and pass `mediator.send`.
    
3. **Add Import Linter contracts** to `pyproject.toml` and wire to CI.
    
4. **Create one vertical slice** (e.g., `users.create`/`users.show`) with command/query/handler and a tiny infra adapter to prove the path.
    
5. **(Optional)** Add `dependency-injector` container to `composition/` so handlers/infra can be wired cleanly as the app grows.
    
6. **Migrate `mug/cli.py`** functionality into a Typer presentation module (or keep it separate and not part of the `mug` entrypoint).
    

If you want, I can generate a small PR-ready patch set (file deletes + minimal code changes) that:

* removes the `__init__.py` namespaces,
    
* wires `users` CLI into the root,
    
* adds the Import Linter block to `pyproject.toml`,
    
* and drops in a simple `users.create`/`users.show` example to validate the end-to-end flow.