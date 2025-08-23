import typer

from mug.modules.users.presentation.public import app as users_app
from .container import bootstrap, exit_code_for, EXIT_OK

app = typer.Typer()
app.add_typer(users_app, name="users")


@app.callback()
def main(ctx: typer.Context) -> None:
    container = bootstrap()
    ctx.obj = container.mediator.send


def run() -> int:
    try:
        app(standalone_mode=False)
        return EXIT_OK
    except Exception as exc:  # pragma: no cover - CLI entry
        return exit_code_for(type(exc))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
