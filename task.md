# Task: Bring `v1` into compliance with `how_to_guide.md` (FAC + single composition root)

## Objectives

1. Enforce PEP 420 namespaces (no `__init__.py` at namespace roots or layer roots).
    
2. Mount module CLIs under a Typer root; presentation calls `send(...)` into a mediator.
    
3. Add Import Linter contracts to lock Clean Architecture boundaries and single composition root.
    
4. Provide one end-to-end “users” slice (create/show) using CQRS + Mediator.
    
5. Remove/relocate any stray CLIs (argparse) so the `mug` entrypoint is Typer-only.
    
6. Add coverage config, basic error taxonomy + exit policy, and a no-op telemetry hook.
    
7. Keep DI confined to `mug/composition` (dependency-injector optional; if not used, ensure registration still happens only in composition).
    

## Constraints

* Do **not** import `mug.composition` from any module.
    
* Modules must not import each other.
    
* Domain must not import application/infra/presentation.
    
* Presentation imports only application.
    
* Infra imports only application.
    
* Keep current build backend (Hatch or Setuptools) as-is; just ensure package discovery works with PEP 420.
    

* * *

## Step-by-step Changes

### 1) Namespace cleanup (PEP 420)

Delete these if present (non-exhaustive; include equivalents for other modules):

```
src/mug/__init__.py
src/mug/modules/__init__.py
src/mug/modules/users/__init__.py
src/mug/modules/users/domain/__init__.py
src/mug/modules/users/application/__init__.py
src/mug/modules/users/infrastructure/__init__.py
src/mug/modules/users/presentation/__init__.py
src/mug/modules/users/composition/__init__.py
```

> Rule: no `__init__.py` at `src/mug` nor at any layer root (`domain|application|infrastructure|presentation|composition`).

If using **setuptools**, ensure:

```toml
[tool.setuptools.packages.find]
where = ["src"]
namespaces = true
include = ["mug*"]
```

If using **hatchling**, ensure the package target includes `src/mug` without requiring `__init__.py`.

* * *

### 2) Minimal mediator (async-ready) in common

Create/ensure:

```
src/mug/common/application/mediator.py
```

```python
from typing import Any, Callable, Dict, Type
import inspect
Handler = Callable[[Any], Any]

class Mediator:
    def __init__(self) -> None:
        self._handlers: Dict[Type[Any], Handler] = {}

    def register(self, message_type: Type[Any], handler: Handler) -> None:
        if message_type in self._handlers:
            raise ValueError(f"Handler already registered for {message_type.__name__}")
        self._handlers[message_type] = handler

    async def send(self, message: Any) -> Any:
        handler = self._handlers.get(type(message))
        if not handler:
            raise KeyError(f"No handler for {type(message).__name__}")
        result = handler(message)
        return await result if inspect.isawaitable(result) else result

Send = Callable[[Any], Any]
```

* * *

### 3) Composition root: bootstrap + Typer root

Create/ensure:

```
src/mug/composition/container.py
```

```python
from mug.common.application.mediator import Mediator
# If you want dependency_injector, you can add it here; otherwise keep it simple.

class AppContainer:
    def __init__(self) -> None:
        self.mediator = Mediator()
        # telemetry, settings, etc. can be attached later

def bootstrap() -> AppContainer:
    c = AppContainer()
    # --- handler registration happens here (see step 4) ---
    return c
```

```
src/mug/composition/__main__.py
```

```python
import typer
from .container import bootstrap
from mug.modules.users.presentation.cli import get_app as get_users_cli

def build_root_app() -> typer.Typer:
    app = typer.Typer(help="Mug CLI", no_args_is_help=True)
    container = bootstrap()
    send = container.mediator.send  # async send; Typer can call via asyncio.run if needed

    app.add_typer(get_users_cli(send), name="users")
    return app

def main() -> int:
    build_root_app()()
    return 0
```

If any legacy CLIs exist (e.g., `mug/cli.py` using argparse), either:

* migrate those commands into `presentation/*` Typer modules, or
    
* exclude them from the `mug` entrypoint (they can remain as separate tools if needed).
    

* * *

### 4) Users module — end-to-end slice

Create/ensure:

**Domain**

```
src/mug/modules/users/domain/users/entities.py
```

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:
    value: str

@dataclass(frozen=True)
class User:
    id: UserId
    name: str
```

```
src/mug/modules/users/domain/users/ports.py
```

```python
from typing import Protocol, Optional
from .entities import User, UserId

class UserWriter(Protocol):
    def add(self, user: User) -> None: ...

class UserReader(Protocol):
    def get(self, user_id: UserId) -> Optional[User]: ...
```

**Application**

```
src/mug/modules/users/application/users/create_user/create_user_command.py
```

```python
from dataclasses import dataclass
from mug.modules.users.domain.users.entities import UserId

@dataclass(frozen=True)
class CreateUserCommand:
    id: UserId
    name: str
```

```
src/mug/modules/users/application/users/create_user/create_user_command_handler.py
```

```python
from mug.modules.users.domain.users.entities import User
from mug.modules.users.domain.users.ports import UserWriter
from .create_user_command import CreateUserCommand

def make_create_user_handler(repo: UserWriter):
    def handle(cmd: CreateUserCommand) -> None:
        repo.add(User(id=cmd.id, name=cmd.name))
    return handle
```

```
src/mug/modules/users/application/users/show_user/show_user_query.py
```

```python
from dataclasses import dataclass
from mug.modules.users.domain.users.entities import UserId

@dataclass(frozen=True)
class ShowUserQuery:
    id: UserId
```

```
src/mug/modules/users/application/users/show_user/show_user_query_handler.py
```

```python
from typing import Optional
from mug.modules.users.domain.users.entities import User
from mug.modules.users.domain.users.ports import UserReader
from .show_user_query import ShowUserQuery

def make_show_user_handler(repo: UserReader):
    def handle(q: ShowUserQuery) -> Optional[User]:
        return repo.get(q.id)
    return handle
```

**Infrastructure**

```
src/mug/modules/users/infrastructure/users/repos_memory.py
```

```python
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

**Presentation (Typer)**

```
src/mug/modules/users/presentation/cli.py
```

```python
import typer
import asyncio
from typing import Callable, Any
from mug.modules.users.domain.users.entities import UserId
from mug.modules.users.application.users.create_user.create_user_command import CreateUserCommand
from mug.modules.users.application.users.show_user.show_user_query import ShowUserQuery

Send = Callable[[Any], Any]

def get_app(send: Send) -> typer.Typer:
    app = typer.Typer(help="User commands")

    @app.command("create")
    def create(user_id: str, name: str) -> None:
        asyncio.run(send(CreateUserCommand(id=UserId(user_id), name=name)))

    @app.command("show")
    def show(user_id: str) -> None:
        u = asyncio.run(send(ShowUserQuery(id=UserId(user_id))))
        typer.echo(f"{u.id.value}: {u.name}" if u else "User not found")

    return app
```

**Register handlers in composition bootstrap**  
Edit:

```
src/mug/composition/container.py
```

```python
# ... inside bootstrap() after creating container c
from mug.modules.users.infrastructure.users.repos_memory import InMemoryUserRepo
from mug.modules.users.application.users.create_user.create_user_command import CreateUserCommand
from mug.modules.users.application.users.create_user.create_user_command_handler import make_create_user_handler
from mug.modules.users.application.users.show_user.show_user_query import ShowUserQuery
from mug.modules.users.application.users.show_user.show_user_query_handler import make_show_user_handler

repo = InMemoryUserRepo()
c.mediator.register(CreateUserCommand, make_create_user_handler(repo))
c.mediator.register(ShowUserQuery,    make_show_user_handler(repo))
return c
```

* * *

### 5) Import Linter contracts

Append to `pyproject.toml` (adapt module names if you have more than `users`):

```toml
[tool.importlinter]
root_package = "mug"

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

[[tool.importlinter.contracts]]
name = "No module imports composition root"
type = "forbidden"
forbidden = [
  "mug.composition",
]
sources = ["mug.modules.users", "mug.common", "mug.modules"]

[[tool.importlinter.contracts]]
name = "Modules are independent"
type = "independence"
modules = ["mug.modules.users"]  # add more as they appear

[[tool.importlinter.contracts]]
name = "Composition may import modules (wiring allowed)"
type = "whitelist"
source = "mug.composition"
allowed = ["mug.modules.users", "mug.common"]
```

Add a simple task runner command (Makefile or Hatch env) to run:

```
lint-imports
```

or

```
python -m importlinter
```

* * *

### 6) Error taxonomy + exit policy + telemetry

Create:

```
src/mug/common/domain/errors.py
```

```python
class DomainError(Exception): ...
class ValidationError(DomainError): ...
class NotFound(DomainError): ...
class Conflict(DomainError): ...
class InfraError(Exception): ...
```

Create:

```
src/mug/composition/exit_policy.py
```

```python
from typing import Type
from mug.common.domain.errors import ValidationError, NotFound, Conflict, DomainError

EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_NOT_FOUND = 3
EXIT_CONFLICT = 4
EXIT_UNKNOWN = 1

def exit_code_for(exc_type: Type[BaseException]) -> int:
    if issubclass(exc_type, ValidationError): return EXIT_VALIDATION
    if issubclass(exc_type, NotFound): return EXIT_NOT_FOUND
    if issubclass(exc_type, Conflict): return EXIT_CONFLICT
    if issubclass(exc_type, DomainError): return EXIT_UNKNOWN
    return EXIT_UNKNOWN
```

Optional telemetry placeholder:

```
src/mug/composition/telemetry.py
```

```python
class Telemetry:
    def on_success(self, cmd_or_query, result) -> None: ...
    def on_error(self, cmd_or_query, exc: BaseException) -> None: ...
```

(Integrate later as needed from `__main__`/handlers.)

* * *

### 7) Coverage config

Append to `pyproject.toml`:

```toml
[tool.coverage.run]
branch = true
source = ["mug"]

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 85
```

* * *

## Remove or migrate legacy argparse CLI

* If `src/mug/cli.py` (or similar) exists and uses `argparse`, migrate commands into `presentation/*` Typer modules, or leave the file but ensure `[project.scripts].mug` points only to `mug.composition.__main__:main`.
    

* * *

## Smoke tests (manual)

Run:

```bash
python -m mug --help
python -m mug users create --user-id usr_alice --name Alice
python -m mug users show --user-id usr_alice
```

Run imports lint:

```bash
python -m importlinter
```

Run coverage (adjust to your runner):

```bash
pytest --maxfail=1 -q
coverage run -m pytest
coverage report -m
```

* * *

## Definition of Done (acceptance criteria)

*  No `__init__.py` at `src/mug` nor at any layer root.
    
*  `mug` entrypoint (`python -m mug`) exposes a Typer root with `users` subcommands.
    
*  `users create/show` work end-to-end using the mediator.
    
*  No cross-module imports; presentation imports only application; infra imports only application; domain is isolated.
    
*  `python -m importlinter` passes with the configured contracts.
    
*  Coverage config present; tests run; coverage ≥ 85% threshold (or file present with threshold ready).
    
*  Any legacy argparse CLI is either migrated to Typer presentation or excluded from the `mug` entrypoint.
    
*  Error taxonomy and exit policy modules exist (even if minimally used).
    
*  Telemetry stub present (no-op is fine).
    

* * *

## Commit plan (suggested)

1. `chore(ns): remove __init__.py at PEP 420 roots`
    
2. `feat(mediator): add async-ready mediator in common`
    
3. `feat(composition): bootstrap + root Typer app, mount users CLI`
    
4. `feat(users): add create/show CQRS + in-memory repo + CLI`
    
5. `chore(importlinter): add CA boundary contracts + tasks`
    
6. `chore(coverage): add coverage config`
    
7. `feat(errors): add error taxonomy + exit policy; add telemetry stub`
    
8. `refactor(cli): migrate/remove argparse sidecar`
    

* * *