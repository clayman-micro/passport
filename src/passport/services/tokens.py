from datetime import datetime, timedelta

import jwt

from passport.domain import TokenType, User
from passport.exceptions import BadToken, TokenExpired


class TokenGenerator:
    __slots__ = ("_private_key",)

    def __init__(self, private_key: str) -> None:
        self._private_key = private_key

    def generate(self, user: User, token_type: TokenType = TokenType.access, expire: int = 600,) -> str:
        now = datetime.utcnow()

        return jwt.encode(
            {
                "user": {"id": user.key, "email": user.email},
                "token_type": token_type.value,
                "iss": "urn:passport",
                "exp": now + timedelta(seconds=expire),
                "iat": now,
            },
            self._private_key,
            algorithm="RS256",
        ).decode("utf-8")


class TokenDecoder:
    __slots__ = ("_public_key",)

    def __init__(self, public_key: str) -> None:
        self._public_key = public_key

    def decode(self, token: str, token_type: TokenType = TokenType.access) -> User:
        try:
            token_data = jwt.decode(token, self._public_key, issuer="urn:passport", algorithms="RS256",)
        except jwt.ExpiredSignatureError:
            raise TokenExpired()
        except jwt.DecodeError:
            raise BadToken()

        if token_data.get("token_type", None) != token_type.value:
            raise BadToken()

        if "user" in token_data:
            try:
                user_key = int(token_data["user"].get("id", None))
            except ValueError:
                raise BadToken()
        else:
            raise BadToken()

        return User(key=user_key, email=token_data["user"].get("email", ""))  # type: ignore
