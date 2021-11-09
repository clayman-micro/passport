import os

import config  # type: ignore
from aiohttp import web
from aiohttp_micro import (  # type: ignore
    AppConfig as BaseConfig,
    setup as setup_micro,
    setup_logging,
    setup_metrics,
)
from aiohttp_storage import setup as setup_storage  # type: ignore

from passport.handlers import auth as auth_endpoints
from passport.handlers.api import (
    keys,
    tokens as token_endpoints,
    users as user_endpoints,
)


class StorageConfig(config.PostgresConfig):
    host = config.StrField(default="localhost", env="POSTGRES_HOST")
    port = config.IntField(default=5432, env="POSTGRES_PORT")
    user = config.StrField(default="postgres", path="postgres-user", env="POSTGRES_USER")
    password = config.StrField(default="postgres", path="postgres-password", env="POSTGRES_PASSWORD")
    database = config.StrField(default="postgres", env="POSTGRES_DATABASE")
    min_pool_size = config.IntField(default=1, env="POSTGRES_MIN_POOL_SIZE")
    max_pool_size = config.IntField(default=2, env="POSTGRES_MAX_POOL_SIZE")

    @property
    def uri(self) -> str:
        return "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            user=self.user, password=self.password, host=self.host, port=self.port, database=self.database,
        )


class SessionConfig(config.Config):
    domain = config.StrField(env="SESSION_DOMAIN")
    cookie = config.StrField(default="session", env="SESSION_COOKIE")
    expire = config.IntField(default=30, env="SESSION_EXPIRE")


class TokenConfig(config.Config):
    access_token_expire = config.IntField(default=900, env="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire = config.IntField(default=43200, env="REFRESH_TOKEN_EXPIRE")
    private_key = config.StrField(path="passport.key", env="TOKEN_PRIVATE_KEY")
    public_key = config.StrField(path="passport.key.pub", env="TOKEN_PUBLIC_KEY")


class AppConfig(BaseConfig):
    db = config.NestedField[StorageConfig](StorageConfig)
    sessions = config.NestedField[SessionConfig](SessionConfig)
    tokens = config.NestedField[TokenConfig](TokenConfig)


def init(app_name: str, config: AppConfig) -> web.Application:
    app = web.Application()

    app["app_root"] = os.path.dirname(__file__)

    setup_micro(app, app_name, config)
    setup_storage(
        app, root=os.path.join(app["app_root"], "storage"), config=app["config"].db,
    )

    setup_logging(app)
    setup_metrics(app)

    # Public user endpoints
    app.router.add_post("/auth/login", auth_endpoints.login, name="auth.login")
    app.router.add_post("/auth/logout", auth_endpoints.logout, name="auth.logout")

    app.router.add_get("/api/keys", keys, name="api.keys")

    # User API endpoints
    app.router.add_get("/api/profile", user_endpoints.profile, name="api.users.profile")
    app.router.add_post("/api/login", user_endpoints.login, name="api.users.login")
    app.router.add_post("/api/register", user_endpoints.register, name="api.users.register")

    # Manage tokens endpoints
    app.router.add_get("/api/tokens/access", token_endpoints.access, name="api.tokens.access")
    app.router.add_post(
        "/api/tokens/refresh", token_endpoints.refresh, name="api.tokens.refresh",
    )

    return app
