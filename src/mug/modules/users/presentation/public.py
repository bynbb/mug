"""Users CLI commands."""

import asyncio
import typer

from mug.common.application.mediator import Send
from mug.modules.users.application.public import CreateUser, GetUser

app = typer.Typer()


@app.command()
def create(
    ctx: typer.Context,
    user_id: str = typer.Option(..., "--user-id"),
    name: str = typer.Option(..., "--name"),
) -> None:
    send: Send = ctx.obj
    asyncio.run(send(CreateUser(user_id=user_id, name=name)))
    typer.echo("OK")


@app.command()
def show(
    ctx: typer.Context,
    user_id: str = typer.Option(..., "--user-id"),
) -> None:
    send: Send = ctx.obj
    user = asyncio.run(send(GetUser(user_id=user_id)))
    typer.echo(f"{user.user_id} {user.name}")
