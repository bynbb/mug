import json
from pathlib import Path
from typing import Dict

from mug.common.domain.errors import Conflict, NotFound
from mug.modules.users.domain.public import User


class InMemoryUserRepo:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("users_db.json")
        self._users: Dict[str, User] = {}
        if self._path.exists():
            data = json.loads(self._path.read_text())
            for uid, record in data.items():
                self._users[uid] = User(**record)

    def _save(self) -> None:
        data = {uid: {"user_id": u.user_id, "name": u.name} for uid, u in self._users.items()}
        self._path.write_text(json.dumps(data))

    def add(self, user: User) -> None:
        if user.user_id in self._users:
            raise Conflict(f"user {user.user_id} exists")
        self._users[user.user_id] = user
        self._save()

    def get(self, user_id: str) -> User:
        try:
            return self._users[user_id]
        except KeyError as exc:
            raise NotFound(f"user {user_id} not found") from exc
