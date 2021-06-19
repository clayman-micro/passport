from aiohttp import web
from aiohttp_micro.web.handlers import json_response  # type: ignore
from marshmallow import fields, Schema  # type: ignore


class KeysResponseSchema(Schema):
    public = fields.Str()


async def keys(request: web.Request) -> web.Response:
    config = request.app["config"]

    schema = KeysResponseSchema()
    response = schema.dump({"public": config.tokens.public_key})

    return json_response(response)
