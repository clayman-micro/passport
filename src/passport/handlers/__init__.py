import functools

from aiohttp import web
from aiohttp_micro.core.exceptions import EntityNotFound  # type: ignore
from aiohttp_micro.core.schemas import EntitySchema  # type: ignore
from marshmallow import fields, Schema

from passport.domain import User
from passport.exceptions import BadToken, TokenExpired
from passport.services.tokens import TokenDecoder
from passport.storage import DBStorage


class UserSchema(EntitySchema):
    entity_cls = User

    email = fields.Str(required=True, description="Email")


class CredentialsPayloadSchema(Schema):
    email = fields.Str(required=True, description="User email")
    password = fields.Str(required=True, description="User password")


class UserResponseSchema(Schema):
    user = fields.Nested(UserSchema, required=True)


def token_required(header: str = "X-ACCESS-TOKEN"):
    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(request: web.Request):
            token = request.headers.get(header, "")

            if not token:
                raise web.HTTPUnauthorized(text="Auth token required")

            try:
                config = request.app["config"]
                decoder = TokenDecoder(public_key=config.tokens.public_key)
                user = decoder.decode(token)
            except (BadToken, TokenExpired):
                raise web.HTTPForbidden

            request["user"] = user

            return await f(request)

        return wrapped

    return wrapper


def session_required(f):
    @functools.wraps(f)
    async def wrapper(request: web.Request):
        config = request.app["config"]

        session_key = request.cookies.get(config.sessions.cookie, None)
        if session_key:
            storage = DBStorage(request.app["db"])

            user_key = await storage.sessions.fetch(key=session_key)

            if user_key:
                try:
                    user = await storage.users.fetch_by_key(key=user_key)
                except EntityNotFound:
                    raise web.HTTPForbidden

                request["user"] = user

                return await f(request)

        raise web.HTTPForbidden

    return wrapper
