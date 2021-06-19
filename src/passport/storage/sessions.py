from datetime import datetime

import sqlalchemy  # type: ignore
from aiohttp_storage.storage import metadata  # type: ignore
from databases import Database

from passport.domain import User
from passport.domain.storage.sessions import SessionRepo


sessions = sqlalchemy.Table(
    "sessions",
    metadata,
    sqlalchemy.Column("key", sqlalchemy.String(44), primary_key=True),
    sqlalchemy.Column("expires", sqlalchemy.DateTime, default=datetime.utcnow),
    sqlalchemy.Column(
        "user", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    ),
)


class SessionDBStorage(SessionRepo):
    def __init__(self, database: Database) -> None:
        self._database = database

    async def fetch(self, key: str) -> int:
        query = sqlalchemy.select([sessions.c.user]).where(sessions.c.key == key)
        user_key = await self._database.fetch_val(query)

        return user_key

    async def add(self, user: User, key: str, expires: datetime) -> None:
        await self._database.execute(
            sessions.insert(), values={"key": key, "user": user.key, "expires": expires},
        )

    async def remove(self, key: str) -> None:
        await self._database.execute(sessions.delete().where(sessions.c.key == key))
