from typing import Protocol

from passport.domain import Permission, User


class UsersRepo(Protocol):
    async def fetch_by_key(self, key: int) -> User:
        ...

    async def fetch_by_email(self, email: str) -> User:
        ...

    async def exists(self, email: str) -> bool:
        ...

    async def add(self, user: User) -> None:
        ...

    async def add_permission(self, user: User, permission: Permission) -> None:
        ...

    async def remove_permission(self, user: User, permission: Permission) -> None:
        ...

    async def save_user(self, email: str, password: str) -> int:
        ...
