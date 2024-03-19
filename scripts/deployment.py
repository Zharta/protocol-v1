import logging
import warnings
import os
import click
from ape.cli import network_option, NetworkBoundCommand

from ape import convert

from ._helpers.deployment import DeploymentManager, Environment

ENV = Environment[os.environ.get("ENV", "local")]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
warnings.filterwarnings("ignore")


def gas_cost(context):
    return {'gas_price': convert('10 gwei', int)}


@click.command(cls=NetworkBoundCommand)
@network_option()
def cli(network):
    print(f"Connected to {network}")

    dm = DeploymentManager(ENV)
    dm.context.gas_func = gas_cost

    changes = set()
    # changes |= {
    #     "eth-grails.loans",
    # }

    dm.deploy(changes, dryrun=True)

    print("Done")

