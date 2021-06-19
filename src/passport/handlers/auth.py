import secrets
from datetime import datetime, timedelta
from typing import Dict

from aiohttp import web
from aiohttp_micro.core.exceptions import EntityNotFound  # type: ignore
from aiohttp_micro.web.handlers import (  # type: ignore
    json_response,
    validate_payload,
)

from passport.exceptions import Forbidden
from passport.handlers import CredentialsPayloadSchema, session_required
from passport.storage import DBStorage
from passport.use_cases.users import LoginUseCase


@validate_payload(CredentialsPayloadSchema)
async def login(payload: Dict[str, str], request: web.Request) -> web.Response:
    use_case = LoginUseCase(app=request.app)

    try:
        user = await use_case.execute(payload["email"], payload["password"])
    except Forbidden:
        raise web.HTTPForbidden()
    except EntityNotFound:
        raise web.HTTPNotFound()

    config = request.app["config"]

    session_key = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=config.sessions.expire)

    storage = DBStorage(database=request.app["db"])
    await storage.sessions.add(user, session_key, expires)

    request.app["logger"].info("User logged in", user=user.email)

    response = json_response({})
    response.set_cookie(
        name=config.sessions.cookie,
        value=session_key,
        max_age=config.sessions.expire * 24 * 60 * 60,
        domain=config.sessions.domain,
        httponly="True",
    )

    return response


@session_required
async def logout(request: web.Request) -> web.Response:
    request.app["logger"].info("User logged out", user=request["user"].email)

    config = request.app["config"]

    redirect = web.HTTPFound(location="/")
    redirect.del_cookie(name=config.sessions.cookie, domain=config.sessions.domain)

    raise redirect
