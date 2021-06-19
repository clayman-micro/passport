from aiohttp_micro.core.exceptions import EntityAlreadyExist  # type: ignore

from passport.domain import User
from passport.domain.storage import Storage
from passport.exceptions import Forbidden


class UserService:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    async def register(self, email: str, password: str) -> User:
        exist = await self.storage.users.exists(email)

        if exist:
            raise EntityAlreadyExist()

        user = User(  # type: ignore
            key=0, email=email, password="", is_superuser=False, permissions=[]
        )
        user.set_password(password)

        await self.storage.users.add(user)

        return user

    async def login(self, email: str, password: str) -> User:
        user = await self.storage.users.fetch_by_email(email)

        is_valid = user.verify_password(password)
        if not is_valid:
            raise Forbidden()

        return user

    async def fetch(self, key: int, active: bool) -> User:
        user = await self.storage.users.fetch_by_key(key)

        return user
