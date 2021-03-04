from typing import Dict

import aiozipkin
from aiohttp import web
from aiohttp_micro.exceptions import (  # type: ignore
    EntityAlreadyExist,
    EntityNotFound,
)
from aiohttp_micro.handlers import (  # type: ignore
    json_response,
    validate_payload,
)
from aiohttp_openapi import (  # type: ignore
    JSONResponse,
    register_operation,
    RequestBody,
)

from passport.domain import TokenType
from passport.exceptions import Forbidden
from passport.handlers import (
    AccessTokenParameter,
    CredentialsPayloadSchema,
    token_required,
    UserResponseSchema,
)
from passport.services.tokens import TokenGenerator
from passport.use_cases.users import LoginUseCase, RegisterUserUseCase


@register_operation(
    description="Register new user",
    request_body=RequestBody(
        description="New user credentials",
        schema=CredentialsPayloadSchema,  # type: ignore
    ),
    responses=(
        JSONResponse(
            description="New user instance",
            schema=UserResponseSchema,  # type: ignore
            status_code=201,
        ),
    ),
)
@validate_payload(CredentialsPayloadSchema)
async def register(
    payload: Dict[str, str], request: web.Request
) -> web.Response:
    use_case = RegisterUserUseCase(app=request.app)

    try:
        user = await use_case.execute(
            email=payload["email"], password=payload["password"]
        )
    except EntityAlreadyExist:
        return json_response({"errors": {"email": "Already exist"}}, status=422)

    schema = UserResponseSchema()
    response = schema.dump({"user": user})

    return json_response(response, status=201)


@register_operation(
    description="Login user",
    request_body=RequestBody(
        description="User credentials",
        schema=CredentialsPayloadSchema,  # type: ignore
    ),
    responses=(
        JSONResponse(
            description="User instance",
            schema=UserResponseSchema,  # type: ignore
        ),
    ),
)
@validate_payload(CredentialsPayloadSchema)
async def login(payload: Dict[str, str], request: web.Request) -> web.Response:
    tracer = request.app[aiozipkin.APP_AIOZIPKIN_KEY]
    span = aiozipkin.request_span(request)
    with tracer.new_child(span.context) as child_span:
        use_case = LoginUseCase(app=request.app)

        try:
            user = await use_case.execute(
                email=payload["email"], password=payload["password"]
            )
        except Forbidden:
            raise web.HTTPForbidden()
        except EntityNotFound:
            raise web.HTTPNotFound()

        config = request.app["config"]
        generator = TokenGenerator(private_key=config.tokens.private_key)

        schema = UserResponseSchema()
        response = schema.dump({"user": user})

        child_span.name("Login user")
        child_span.tag("user_id", user.key)

    return json_response(
        response,
        headers={
            "X-ACCESS-TOKEN": generator.generate(
                user, expire=config.tokens.access_token_expire
            ),
            "X-REFRESH-TOKEN": generator.generate(
                user,
                token_type=TokenType.refresh,
                expire=config.tokens.refresh_token_expire,
            ),
        },
    )


@register_operation(
    description="User profile details",
    parameters=(AccessTokenParameter,),
    responses=(
        JSONResponse(
            description="User instance",
            schema=UserResponseSchema,  # type: ignore
        ),
    ),
)
@token_required()
async def profile(request: web.Request) -> web.Response:
    schema = UserResponseSchema()
    response = schema.dump({"user": request["user"]})

    return json_response(response)
