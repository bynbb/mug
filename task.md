# How To Implement Fast Asymmetric Coupling (FAC) in **Mug**

> **Status:** Consolidated and final. This document replaces earlier drafts and scattered addendums.  
> **Goal:** Provide one clear, conflict-free implementation plan for Mug that follows **Fast Asymmetric Coupling (FAC)** with a **single composition root**, **modules-as-services**, **Mediator/CQRS**, and **Import Linter–enforced boundaries** — while complying with the current requirements (e.g., PEP 420 namespaces, Typer CLI, no service locator).

* * *

## 0) Design Principles (FAC)

* **Asymmetric coupling:** imports flow **out → in**: `presentation → application → domain`.  Infrastructure depends **only** on application. Composition wires everything.
    
* **Single composition root:** all wiring, process configuration, and CLI mounting live **only** in `mug/composition/`.
    
* **Modules as services:** each feature lives in `mug/modules/<feature>/` with Clean Architecture slices: `composition, domain, application, infrastructure, presentation`.
    
* **Mediator/CQRS:** presentation sends **commands/queries**; application provides **handlers/use cases**; composition registers handlers into a mediator.
    
* **Boundaries enforced by contracts & tests (no facades).**
    
* **No service locator:** modules never import a container or call `container.get(...)`. DI is owned by the composition root only.
    

* * *

## 1) Final Target Repository Shape

```
src/
  mug/                              # PEP 420 namespace root (NO __init__.py here)
    composition/                    # CLI entry + bootstrap + services registry
    common/                         # cross-cutting (domain/application abstractions, infra/presentation helpers)
      domain/                       # base domain exceptions & types (no I/O)
      application/                  # mediator, base app exceptions, ports
      infrastructure/               # helpers/adapters (e.g. telemetry/http/paths)
      presentation/                 # CLI helpers (Typer utilities)
    modules/                        # feature modules
      system/
        composition/                # module registration + Typer app provider
        domain/                     # entities, value objects, ports
        application/                # commands/queries/handlers (organized by use-case)
        infrastructure/             # adapters implementing domain/app ports
        presentation/               # Typer commands (small, I/O-free on import)
      users/
        composition/
        domain/
        application/
        infrastructure/
        presentation/
```

**Namespace rules**

* `src/mug/` is a **PEP 420 namespace**: **do not** create `src/mug/__init__.py`.
    
* **Layer roots** (`.../<module>/{domain,application,infrastructure,presentation}`) are **namespace packages** as well: **do not** add `__init__.py` at these roots.
    
* Subpackages for specific features/use-cases may be added; prefer **omitting** `__init__.py` unless you intentionally need a true package.
    

* * *

## 2) Dependency Rules (Clean Architecture)

* **Domain** imports **nothing** from `{application, infrastructure, presentation, composition}`.
    
* **Application** imports **only its own domain** (optionally `mug.common.domain`).
    
* **Infrastructure** imports **only** its module’s **application** contracts.
    
* **Presentation** imports **only** its module’s **application**.
    
* **Composition** imports application/infrastructure to wire (never domain directly).
    
* **Modules are independent**; no cross-module imports.
    
* **No one imports composition** (composition imports modules).
    

Enforce these with **Import Linter** (see §10).

* * *

## 3) Toolchain & Packaging (Full `pyproject.toml`)

> **Embedded verbatim from your provided file.**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mug"
version = "0.0.4"
description = "Mug — Fast Asymmetric Coupling implementation with a single composition root"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = [
  "xmlschema>=2.0",
  "typer>=0.12,<1.0",
  "click>=8.1,<9.0",
  "dependency-injector>=4.41",
]

[project.optional-dependencies]
dev = [
  "import-linter>=2.0,<3.0",
  "coverage[toml]>=7.6,<8.0",
]

[project.scripts]
mug = "mug.composition.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true
include = ["mug*"]

[tool.coverage.run]
branch = true
source = ["mug"]

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 85

[tool.importlinter]
root_package = "mug"

[[tool.importlinter.contracts]]
name = "System module respects CA layers"
type = "layers"
layers = [
    "mug.modules.system.presentation",
    "mug.modules.system.infrastructure",
    "mug.modules.system.application",
    "mug.modules.system.domain",
]
allow_imports = ["mug.modules.system.infrastructure -> mug.modules.system.application"]
ignore_imports = ["mug.modules.system.composition -> *"]

[[tool.importlinter.contracts]]
name = "Users module respects CA layers"
type = "layers"
layers = [
    "mug.modules.users.presentation",
    "mug.modules.users.infrastructure",
    "mug.modules.users.application",
    "mug.modules.users.domain",
]
allow_imports = ["mug.modules.users.infrastructure -> mug.modules.users.application"]
ignore_imports = ["mug.modules.users.composition -> *"]

[[tool.importlinter.contracts]]
name = "No module imports composition root (single DI root)"
type = "forbidden"
forbidden = [
  "mug.composition",
  "mug.modules.system.composition",
  "mug.modules.users.composition",
]
sources = ["mug.modules.system", "mug.modules.users", "mug.common", "mug.modules"]

[[tool.importlinter.contracts]]
name = "Modules are independent (no cross-module imports)"
type = "independence"
modules = ["mug.modules.system", "mug.modules.users"]

[[tool.importlinter.contracts]]
name = "Composition may import modules (wiring allowed)"
type = "whitelist"
source = "mug.composition"
allowed = ["mug.modules.system", "mug.modules.users", "mug.common"]

[[tool.importlinter.contracts]]
name = "No DI framework inside modules"
type = "forbidden"
forbidden = ["dependency_injector"]
sources = [
  "mug.modules.system",
  "mug.modules.users",
  "mug.common",
]
```

* * *

## 4) Cross-Cutting: Common Layer

Keep **common** focused on abstractions and helpers only (no concrete business wiring). Suggested modules: base domain/app exceptions, simple mediator, CLI helpers, infra helpers. **Domain/Application must not import from common/presentation or common/infrastructure.**

**Minimal mediator:**

```python
# src/mug/common/application/mediator.py
from typing import Any, Callable, Dict, Type

Handler = Callable[[Any], Any]

class Mediator:
    def __init__(self) -> None:
        self._handlers: Dict[Type[Any], Handler] = {}

    def register(self, message_type: Type[Any], handler: Handler) -> None:
        self._handlers[message_type] = handler

    def send(self, message: Any) -> Any:
        handler = self._handlers.get(type(message))
        if not handler:
            raise KeyError(f"No handler for {type(message).__name__}")
        return handler(message)
```

* * *

## 5) Composition Root (with `dependency-injector`) + Typer Root

> `dependency-injector` is confined to **composition**. Modules do **not** import it.

```python
# src/mug/composition/container.py
from dependency_injector import containers, providers
from mug.common.application.mediator import Mediator

# System
from mug.modules.system.infrastructure.app_version.version_reader_metadata import MetadataVersionReader
from mug.modules.system.application.app_version.get_app_version.get_app_version_query_handler import make_get_app_version_handler
from mug.modules.system.application.app_version.get_app_version.get_app_version_query import GetAppVersionQuery

# Users
from mug.modules.users.infrastructure.users.repos_memory import InMemoryUserRepo
from mug.modules.users.application.users.create_user.create_user_command import CreateUserCommand
from mug.modules.users.application.users.create_user.create_user_command_handler import make_create_user_handler
from mug.modules.users.application.users.show_user.show_user_query import ShowUserQuery
from mug.modules.users.application.users.show_user.show_user_query_handler import make_show_user_handler

class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    mediator = providers.Singleton(Mediator)

    # System providers
    version_reader = providers.Singleton(MetadataVersionReader)
    get_app_version_handler = providers.Factory(
        make_get_app_version_handler, reader=version_reader
    )

    # Users providers
    users_repo = providers.Singleton(InMemoryUserRepo)
    create_user_handler = providers.Factory(make_create_user_handler, repo=users_repo)
    show_user_handler   = providers.Factory(make_show_user_handler, repo=users_repo)

def bootstrap() -> AppContainer:
    container = AppContainer()
    mediator = container.mediator()
    mediator.register(GetAppVersionQuery, container.get_app_version_handler())
    mediator.register(CreateUserCommand,  container.create_user_handler())
    mediator.register(ShowUserQuery,      container.show_user_handler())
    return container
```

```python
# src/mug/composition/__main__.py
import typer
from .container import bootstrap
from mug.modules.system.presentation.app_version.cli import get_app as get_system_cli
from mug.modules.users.presentation.users.cli import  get_app as get_users_cli

def build_root_app() -> typer.Typer:
    app = typer.Typer(help="Mug CLI", no_args_is_help=True)
    container = bootstrap()
    send = container.mediator().send
    app.add_typer(get_system_cli(send), name="system")
    app.add_typer(get_users_cli(send),  name="users")
    return app

def main() -> int:
    build_root_app()()
    return 0
```

* * *

## 6) Modules as Services — Structure & Examples

> The code below mirrors your original layout but adds DI-agnostic surfaces.

### 6.1 `system` module (feature: app_version)

**Domain**

```python
# modules/system/domain/app_version/entities.py
from dataclasses import dataclass
@dataclass(frozen=True)
class AppVersion:
    major: int; minor: int; patch: int; raw: str
    def __str__(self) -> str: return self.raw
```

```python
# modules/system/domain/app_version/ports.py
from typing import Protocol
from .entities import AppVersion
class VersionReader(Protocol):
    def get(self, package_name: str) -> AppVersion: ...
```

**Application**

```python
# modules/system/application/app_version/get_app_version/get_app_version_query.py
from dataclasses import dataclass
@dataclass(frozen=True)
class GetAppVersionQuery:
    package_name: str = "mug"
```

```python
# modules/system/application/app_version/get_app_version/get_app_version_query_handler.py
from mug.modules.system.domain.app_version.ports import VersionReader
from .get_app_version_query import GetAppVersionQuery

def make_get_app_version_handler(reader: VersionReader):
    def handle(query: GetAppVersionQuery):
        return reader.get(query.package_name)
    return handle
```

**Infrastructure**

```python
# modules/system/infrastructure/app_version/version_reader_metadata.py
import importlib.metadata as md
from mug.modules.system.domain.app_version.entities import AppVersion
from mug.modules.system.domain.app_version.ports import VersionReader

class MetadataVersionReader(VersionReader):
    def get(self, package_name: str) -> AppVersion:
        raw = md.version(package_name)
        canonical = raw.split("+", 1)[0].split("-", 1)[0]
        parts = [int(p) for p in canonical.split(".")[:3]]
        major, minor, patch = (parts + [0, 0, 0])[:3]
        return AppVersion(major=major, minor=minor, patch=patch, raw=raw)
```

**Presentation (Typer)**

```python
# modules/system/presentation/app_version/cli.py
import typer
from mug.common.application.mediator import Send
from mug.modules.system.application.app_version.get_app_version.get_app_version_query import GetAppVersionQuery

def get_app(send: Send) -> typer.Typer:
    app = typer.Typer(help="System commands")
    @app.command("version")
    def version() -> None:
        v = send(GetAppVersionQuery())
        typer.echo(str(v))
    return app
```

**Module DI surface (DI-agnostic):**

```python
# modules/system/composition/di.py
from mug.composition.bootstrap import AppContainer
from mug.modules.system.application.app_version.get_app_version.get_app_version_query import GetAppVersionQuery
from mug.modules.system.application.app_version.get_app_version.get_app_version_query_handler import make_get_app_version_handler
from mug.modules.system.infrastructure.app_version.version_reader_metadata import MetadataVersionReader
from mug.modules.system.presentation.app_version.cli import get_app as get_system_cli

def register(app: AppContainer) -> None:
    reader = MetadataVersionReader()
    app.mediator.register(GetAppVersionQuery, make_get_app_version_handler(reader))

def get_cli(app: AppContainer):
    return get_system_cli(app.mediator.send)
```

### 6.2 `users` module

**Domain / Application / Infrastructure / Presentation** (unchanged in shape, shown here for completeness):

```python
# modules/users/domain/users/entities.py
from dataclasses import dataclass
@dataclass(frozen=True) class UserId: value: str
@dataclass(frozen=True) class User: id: UserId; name: str
```

```python
# modules/users/domain/users/ports.py
from typing import Protocol, Optional
from .entities import User, UserId
class UserWriter(Protocol):  def add(self, user: User) -> None: ...
class UserReader(Protocol):  def get(self, user_id: UserId) -> Optional[User]: ...
```

```python
# modules/users/application/users/create_user/create_user_command.py
from dataclasses import dataclass
from mug.modules.users.domain.users.entities import UserId
@dataclass(frozen=True) class CreateUserCommand: id: UserId; name: str
```

```python
# modules/users/application/users/create_user/create_user_command_handler.py
from mug.modules.users.domain.users.entities import User
from mug.modules.users.domain.users.ports import UserWriter
from .create_user_command import CreateUserCommand
def make_create_user_handler(repo: UserWriter):
    def handle(cmd: CreateUserCommand) -> None:
        repo.add(User(id=cmd.id, name=cmd.name))
    return handle
```

```python
# modules/users/application/users/show_user/show_user_query.py
from dataclasses import dataclass
from mug.modules.users.domain.users.entities import UserId
@dataclass(frozen=True) class ShowUserQuery: id: UserId
```

```python
# modules/users/application/users/show_user/show_user_query_handler.py
from typing import Optional
from mug.modules.users.domain.users.entities import User
from mug.modules.users.domain.users.ports import UserReader
from .show_user_query import ShowUserQuery
def make_show_user_handler(repo: UserReader):
    def handle(q: ShowUserQuery) -> Optional[User]:
        return repo.get(q.id)
    return handle
```

```python
# modules/users/infrastructure/users/repos_memory.py
from typing import Dict, Optional
from mug.modules.users.domain.users.entities import User, UserId
from mug.modules.users.domain.users.ports import UserReader, UserWriter
class InMemoryUserRepo(UserWriter, UserReader):
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
    def add(self, user: User) -> None:
        self._users[user.id.value] = user
    def get(self, user_id: UserId) -> Optional[User]:
        return self._users.get(user_id.value)
```

```python
# modules/users/presentation/users/cli.py
import typer
from mug.common.application.mediator import Send
from mug.modules.users.domain.users.entities import UserId
from mug.modules.users.application.users.create_user.create_user_command import CreateUserCommand
from mug.modules.users.application.users.show_user.show_user_query import ShowUserQuery
def get_app(send: Send) -> typer.Typer:
    app = typer.Typer(help="User commands")
    @app.command("create")
    def create(user_id: str, name: str) -> None:
        send(CreateUserCommand(id=UserId(user_id), name=name))
    @app.command("show")
    def show(user_id: str) -> None:
        u = send(ShowUserQuery(id=UserId(user_id)))
        typer.echo(f"{u.id.value}: {u.name}" if u else "User not found")
    return app
```

**Module DI surface:**

```python
# modules/users/composition/di.py
from mug.composition.bootstrap import AppContainer
from mug.modules.users.application.users.create_user.create_user_command import CreateUserCommand
from mug.modules.users.application.users.create_user.create_user_command_handler import make_create_user_handler
from mug.modules.users.application.users.show_user.show_user_query import ShowUserQuery
from mug.modules.users.application.users.show_user.show_user_query_handler import make_show_user_handler
from mug.modules.users.infrastructure.users.repos_memory import InMemoryUserRepo
from mug.modules.users.presentation.users.cli import get_app as get_users_cli

def register(app: AppContainer) -> None:
    repo = InMemoryUserRepo()
    app.mediator.register(CreateUserCommand, make_create_user_handler(repo))
    app.mediator.register(ShowUserQuery,    make_show_user_handler(repo))

def get_cli(app: AppContainer):
    return get_users_cli(app.mediator.send)
```

* * *

## 7) CLI Contracts (Typer)

* Only **composition** and **presentation** slices may import Typer/Click.
    
* Importing `presentation/*` performs **no I/O** or global side effects; Typer apps are **built lazily**.
    
* Root CLI shows **module groups** (e.g., `users`) and supports shell completion.
    
* CLI handlers are **thin**: parse args → `send()` → print.
    

**Smoke checks:**

```bash
python -m mug --help
python -m mug system version
python -m mug users create --user-id usr_alice --name Alice
python -m mug users show --user-id usr_alice
```

* * *

## 8) Anti-Patterns (Prohibitions)

* No `dependency_injector` under `mug/modules/**`; if used, it must be confined to **composition** only.
    
* No service-locator lookups (`container.get(...)`, `providers.*(...)`) from application/presentation code.
    
* No cross-module internal imports.
    
* Domain & Application don’t perform filesystem/network I/O or read process configuration.
    

* * *

## 9) Observability & Runtime Invariants

* Provide a **telemetry hook** in composition (even a no-op) for successes/errors/timings.
    
* Map exceptions to exit codes consistently.
    

* * *

## 10) Import Linter — Contracts & CI Gate

Contracts (also included in `pyproject.toml` above). Run `lint-imports` when `MUG_RUN_IMPORT_LINTER=1`. Add a weekly canary with unpinned tool versions.

* * *

## 11) Implementation Plan — **Create Each File Once**

> Don’t “stub now, fill later.” Write files in their final intended form; use scripts to generate boilerplate.

**Step 1 — Prepare the repo** (Python 3.11+, fresh venv).  
**Step 2 — Scaffolding** (dirs only; **no `__init__.py`** at namespace roots).  
**Step 3 — Common layer** (exceptions, mediator, helpers).  
**Step 4 — Composition root** (services registry, container + telemetry, Typer root).  
**Step 5 — System module** (app_version end-to-end + DI registration).  
**Step 6 — Users module** (create/show + DI + Typer sub-app).  
**Step 7 — Tooling & CI** (coverage, import-linter).  
**Step 8 — Smoke tests** (CLI works as above).

* * *

## 12) Conventions

* **snake_case** for files/folders; `PascalCase` only for classes.
    
* **CLI-only** presentation here; HTTP out of scope.
    
* Prefer absolute imports within `mug` for clarity.
    

* * *

## 13) Optional Data (CQRS) & DB Conventions (Heads-Up)

* DDL under `.../infrastructure/db/ddl/` (loadable via resources).
    
* DB path: `.mug/db/<module>/<yyyy-mm-dd>-<schema>.sqlite`.
    
* Use `STRICT` tables, `PRAGMA foreign_keys=ON`.
    
* Keep CQRS separation clean.
    

* * *

## 14) Quick Verification Checklist

* **Packaging:** PEP 420 namespaces; no `__init__.py` at `src/mug` or layer roots; Setuptools `namespaces = true`.
    
* **Entry:** `mug.composition.__main__:main`; Typer root mounts module apps.
    
* **DI:** only in composition; modules expose `register(app)` and `get_cli(app)`.
    
* **Rules:** presentation→application→domain; infrastructure→application; modules independent; no imports into composition; contracts green.
    
* **CLI:** users group visible; handlers mapped; exit code policy consistent; **no service locator** anywhere.
    

* * *

# Addendum — Concrete Improvements (Low Hanging Fruit)

This addendum supplements the main design with pragmatic refinements. These are not required for correctness, but they strengthen guardrails, simplify cross-module work, and reduce future refactors.

* * *

## 1. Async-Ready Mediator

* Extend the `Mediator` to support both synchronous and asynchronous handlers.
    
* Prevents disruptive rewrites once I/O-bound use cases (DB, HTTP, queues) appear.
    
* Pattern: detect if a handler result is awaitable, then `await` it.
    

```python
import inspect, asyncio

async def send(self, message: Any) -> Any:
    handler = self._handlers.get(type(message))
    if not handler:
        raise KeyError(f"No handler for {type(message).__name__}")
    result = handler(message)
    if inspect.isawaitable(result):
        return await result
    return result
```

* Optionally split buses:
    
    * `CommandBus` → `dispatch(command) -> None`
        
    * `QueryBus` → `ask(query) -> T`
        
* Introduce a `Result[T, E]` type to capture expected errors without exceptions.
    

* * *

## 2. Stronger Import Contracts

Enhance Import Linter usage to prevent drift:

* **Domain/Application** must never import from `mug.common.infrastructure` or `mug.common.presentation`.
    
* **Only composition** may import `mug.composition.*`.
    
* Retain the existing ban on `dependency_injector` outside composition.
    

* * *

## 3. Error Taxonomy & Exit Policy

* Define a shared hierarchy: `DomainError`, `ValidationError`, `NotFound`, `Conflict`, `InfraError`.
    
* Centralize exit-code mapping (e.g., `ExitPolicy` in composition) so CLI code only raises/handles these classes.
    
* Result: consistent CLI output and simpler testing.
    

* * *

## 4. Configuration & Lifecycle Hooks

* Introduce a `Settings` object in composition (12-factor style), passed into providers.
    
* Add lifecycle management:
    
    * `start()/stop()` or context managers for infra resources (DB pools, HTTP clients).
        
    * Ensure graceful shutdown for CLI.
        
* Define a telemetry interface here too (default no-op), so success/failure/timing hooks are pluggable.
    

* * *

## 5. Cross-Module Collaboration Pattern

Modules must remain independent, but real features often span boundaries. To prevent “just one import” violations:

* **Preferred:** Domain events raised in application, published by composition, and consumed by other modules’ handlers.
    
* **Alternative:** App-level ports (interfaces) defined in one module, implemented and bound in composition.
    

Provide one minimal example so teams don’t improvise.

* * *

## 6. Developer Ergonomics

* Add a scaffold command: `mug new-module <name>` → generates `composition/`, `domain/`, `application/`, `infrastructure/`, `presentation/` plus Import Linter entries.
    
* Configure `ruff`, `mypy` (with namespace awareness), and `py.typed` for type checking.
    
* In CI: run `import-linter`, `mypy`, `ruff`, `coverage`, plus a weekly “canary” job with unpinned versions (to detect breakages early).
    

* * *

## 7. Testing Strategy

Define a clear three-layer approach:

* **Unit:** test domain entities and handlers with fake ports.
    
* **Contract:** test infra adapters against their port expectations.
    
* **Integration:** boot the composition root and drive it through CLI commands.
    

Add a `conftest.py` helper to spin up a test container with fake providers.

* * *

## 8. Small Code Tweaks

* In `Mediator.register`, raise or warn if a handler is overwritten silently.
    
* Use `Mapping[Type[Any], Handler]` instead of `Dict` for type clarity.
    
* Define `Send = Callable[[Any], Any]` centrally (used in CLI).
    
* Be explicit about whether mediator matches exact types vs. subclasses.
    

* * *

✅ These improvements are incremental and safe to add independently. Together they provide:

* Async readiness,
    
* Stronger boundary enforcement,
    
* Clearer error handling,
    
* Cleaner cross-module collaboration,
    
* Better dev/test ergonomics.
    

* * *