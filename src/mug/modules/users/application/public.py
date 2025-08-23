from dataclasses import dataclass
from typing import Protocol

from mug.modules.users.domain.public import User


class UserRepo(Protocol):
    def add(self, user: User) -> None:
        ...

    def get(self, user_id: str) -> User:
        ...


@dataclass
class CreateUser:
    user_id: str
    name: str


@dataclass
class GetUser:
    user_id: str


def make_create_user_handler(repo: UserRepo):
    def handler(cmd: CreateUser) -> None:
        user = User(user_id=cmd.user_id, name=cmd.name)
        repo.add(user)
    return handler


def make_get_user_handler(repo: UserRepo):
    def handler(query: GetUser) -> User:
        return repo.get(query.user_id)
    return handler
