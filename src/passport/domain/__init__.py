from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from aiohttp_micro.core.entities import Entity  # type: ignore
from passlib.handlers.pbkdf2 import pbkdf2_sha512  # type: ignore


class TokenType(Enum):
    access = "access"
    refresh = "refresh"


@dataclass
class Permission(Entity):
    name: str


@dataclass
class User(Entity):
    email: str
    password: Optional[str] = None
    is_superuser: bool = False
    permissions: List[Permission] = field(default_factory=list)

    def set_password(self, password: str) -> None:
        self.password = pbkdf2_sha512.encrypt(password, rounds=10000, salt_size=10)

    def verify_password(self, password: str) -> bool:
        try:
            valid = pbkdf2_sha512.verify(password, self.password)
        except ValueError:
            valid = False
        return valid
