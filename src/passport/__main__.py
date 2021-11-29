from pathlib import Path

import click
import uvloop  # type: ignore
from aiohttp_micro.cli.server import server  # type: ignore
from aiohttp_storage.management.storage import storage  # type: ignore
from config import EnvValueProvider, FileValueProvider, load  # type: ignore

from passport.app import init
from passport.config import AppConfig, VaultConfig, VaultProvider


@click.group()
@click.option("--conf-dir", default=None)
@click.option("--debug", default=False, is_flag=True)
@click.pass_context
def cli(ctx, conf_dir: str = None, debug: bool = False) -> None:
    uvloop.install()

    if conf_dir:
        conf_path = Path(conf_dir)
    else:
        conf_path = Path.cwd()

    vault_config = VaultConfig()
    load(vault_config, providers=[EnvValueProvider()])

    config = AppConfig(
        defaults={
            "debug": debug,
            "db": {"user": "passport", "password": "passport", "database": "passport"},
            "tokens": {"access_token_expire": 900, "refresh_token_expire": 43200},
            "sessions": {"domain": ".clayman.pro", "cookie": "session", "expire": 30},
        }
    )
    load(
        config,
        providers=[
            VaultProvider(config=vault_config, mount_point="credentials"),
            FileValueProvider(conf_path),
            EnvValueProvider(),
        ],
    )

    app = init("passport", config)

    if config.debug:
        app["logger"].debug("Application config", db=config.db.uri, sentry=config.sentry_dsn)

    ctx.obj["app"] = app
    ctx.obj["config"] = config


cli.add_command(server, name="server")
cli.add_command(storage, name="storage")


if __name__ == "__main__":
    cli(obj={})
