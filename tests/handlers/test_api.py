from datetime import datetime, timedelta
from typing import Dict

import jwt
import orjson  # type: ignore
import pytest  # type: ignore
from passlib.handlers.pbkdf2 import pbkdf2_sha512  # type: ignore

from passport.domain import TokenType, User
from passport.services.tokens import TokenGenerator
from passport.storage.users import users as users_table


def prepare_request(data, json=False):
    headers = {}
    if json:
        data = orjson.dumps(data)
        headers = {"Content-Type": "application/json"}

    return {"data": data, "headers": headers}


@pytest.fixture(scope="function")
def prepare_user():
    async def go(user: Dict, app):
        data: Dict = user.copy()
        data.setdefault("is_active", True)

        key = await app["db"].fetch_val(
            users_table.insert().returning(users_table.c.id),
            values={
                "email": data["email"],
                "password": pbkdf2_sha512.encrypt(data["password"], rounds=10000, salt_size=10),
                "is_active": data["is_active"],
                "created_on": datetime.now(),
            },
        )

        return User(key=key, email=data["email"], password=data["password"])  # type: ignore

    return go


@pytest.mark.integration
@pytest.mark.parametrize("json", [True, False])
async def test_registration_success(aiohttp_client, app, json):
    data = {"email": "john@testing.com", "password": "top-secret"}
    client = await aiohttp_client(app)

    url = app.router.named_resources()["api.users.register"].url_for()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 201


@pytest.mark.integration
@pytest.mark.parametrize("json", [True, False])
async def test_registration_failed_without_password(aiohttp_client, app, json):
    data = {"email": "john@testing.com"}
    client = await aiohttp_client(app)

    url = app.router.named_resources()["api.users.register"].url_for()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 422


@pytest.mark.integration
@pytest.mark.parametrize("json", [True, False])
async def test_registration_failed_already_existed(aiohttp_client, app, prepare_user, json):
    data = {"email": "john@testing.com", "password": "top-secret"}
    client = await aiohttp_client(app)

    await prepare_user({"email": "john@testing.com", "password": "top-secret"}, app)

    url = app.router.named_resources()["api.users.register"].url_for()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 422


@pytest.mark.integration
@pytest.mark.parametrize("json", [True, False])
async def test_login_success(aiohttp_client, app, prepare_user, json):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.users.login"].url_for()

    data = {"email": "john@testing.com", "password": "top-secret"}
    await prepare_user(data, app)

    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 200
    assert "X-ACCESS-TOKEN" in resp.headers
    assert "X-REFRESH-TOKEN" in resp.headers


@pytest.mark.integration
@pytest.mark.parametrize("json", [True, False])
@pytest.mark.parametrize("password", ["", "wrong-password"])
async def test_login_failed(aiohttp_client, app, prepare_user, json, password):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.users.login"].url_for()

    email = "john@testing.com"

    await prepare_user({"email": email, "password": "top-secret"}, app)

    payload = {"email": email, "password": password}
    resp = await client.post(url, **prepare_request(payload, json))
    assert resp.status == 403


@pytest.mark.integration
@pytest.mark.parametrize("json", [True, False])
async def test_login_unregistered(aiohttp_client, app, prepare_user, json):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.users.login"].url_for()

    payload = {"email": "peter@missing.com", "password": "some-secret"}
    resp = await client.post(url, **prepare_request(payload, json))
    assert resp.status == 404


@pytest.mark.integration
async def test_refresh_success(aiohttp_client, app, prepare_user):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.tokens.refresh"].url_for()

    user = await prepare_user({"email": "john@testing.com", "password": "top-secret"}, app)

    generator = TokenGenerator(private_key=app["config"].tokens.private_key)
    refresh_token = generator.generate(
        user, token_type=TokenType.refresh, expire=app["config"].tokens.refresh_token_expire,
    )

    headers = {"X-REFRESH-TOKEN": refresh_token}
    resp = await client.post(url, headers=headers)
    assert resp.status == 200
    assert "X-ACCESS-TOKEN" in resp.headers

    access_token = resp.headers["X-ACCESS-TOKEN"]
    token = jwt.decode(access_token, app["config"].tokens.public_key, algorithms="RS256")
    assert token["user"]["id"] == user.key
    assert token["token_type"] == "access"


@pytest.mark.integration
async def test_refresh_failed_with_wrong_token_type(aiohttp_client, app, prepare_user):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.tokens.refresh"].url_for()

    user = await prepare_user({"email": "john@testing.com", "password": "top-secret"}, app)

    generator = TokenGenerator(private_key=app["config"].tokens.private_key)
    refresh_token = generator.generate(
        user, token_type=TokenType.access, expire=app["config"].tokens.refresh_token_expire,
    )

    headers = {"X-REFRESH-TOKEN": refresh_token}
    resp = await client.post(url, headers=headers)
    assert resp.status == 403


@pytest.mark.integration
@pytest.mark.parametrize("user_id", ["", 0, "foo" "2", None])
async def test_refresh_failed(aiohttp_client, app, prepare_user, user_id):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.tokens.refresh"].url_for()

    now = datetime.utcnow()

    refresh_token = jwt.encode(
        {
            "id": user_id,
            "email": "",
            "token_type": TokenType.refresh.value,
            "iss": "urn:passport",
            "exp": now + timedelta(seconds=app["config"].tokens.refresh_token_expire),
            "iat": now,
        },
        app["config"].tokens.private_key,
        algorithm="RS256",
    )

    headers = {"X-REFRESH-TOKEN": refresh_token}
    resp = await client.post(url, headers=headers)
    assert resp.status == 403


@pytest.mark.integration
async def test_refresh_failed_for_inactive(aiohttp_client, app, prepare_user):
    client = await aiohttp_client(app)
    url = app.router.named_resources()["api.tokens.refresh"].url_for()

    user = await prepare_user({"email": "john@testing.com", "password": "top-secret", "is_active": False}, app,)

    generator = TokenGenerator(private_key=app["config"].tokens.private_key)
    refresh_token = generator.generate(
        user, token_type=TokenType.refresh, expire=app["config"].tokens.refresh_token_expire,
    )

    headers = {"X-REFRESH-TOKEN": refresh_token}
    resp = await client.post(url, headers=headers)
    assert resp.status == 403
