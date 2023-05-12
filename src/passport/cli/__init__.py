from importlib.metadata import distribution

import click
import uvloop

from passport.app import create_container, init
from passport.cli.server import server
from passport.logging import configure_logging


@click.group()
@click.option("--debug", is_flag=True, default=False, envvar="DEBUG")
@click.pass_context
def cli(ctx: click.Context, debug: bool = False) -> None:
    """Prepare application entry point for command line interface.

    Args:
        ctx: Current command line application context.
        debug: Run application in debug mode.
    """
    uvloop.install()

    dist = distribution("passport")

    ctx.obj["app"] = init(
        dist=dist,
        container=create_container(
            logger=configure_logging(dist=dist, debug=debug),
        ),
        debug=debug,
    )


cli.add_command(server, name="server")
