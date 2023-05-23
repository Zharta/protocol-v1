import os
from scripts.deployment import DeploymentManager, Environment

ENV = Environment[os.environ.get("ENV", "local")]


def ape_init_extras(network):
    dm = DeploymentManager(ENV)

    globals()["dm"] = dm
    globals()["owner"] = dm.owner
    for k, v in dm.context.contract.items():
        globals()[k.replace(".", "_").replace("-", "_")] = v.contract
        print(k.replace(".", "_"), v.contract)
    for k, v in dm.context.config.items():
        globals()[k.replace(".", "_").replace("-", "_")] = v
