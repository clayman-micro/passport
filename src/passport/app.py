import os

from aiohttp import web
from aiohttp_micro import setup as setup_micro
from aiohttp_micro import setup_logging, setup_metrics
from aiohttp_storage import setup as setup_storage  # type: ignore

from passport.config import AppConfig
from passport.handlers import auth as auth_endpoints
from passport.handlers.api import keys
from passport.handlers.api import tokens as token_endpoints
from passport.handlers.api import users as user_endpoints


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
