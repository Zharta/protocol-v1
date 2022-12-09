import json
import logging
import os

from typing import Any
from brownie import ERC721, accounts
from pathlib import Path

from .helpers.dependency import DependencyManager
from .helpers.types import (
    ContractConfig,
    DeploymentContext,
    Environment,
    GenericExternalContract,
    InternalContract,
    NFT,
    Token,
)
from .helpers.contracts import (
    LendingPoolCoreContract,
    LendingPoolPeripheralContract,
    CollateralVaultCoreContract,
    CollateralVaultPeripheralContract,
    LoansCoreContract,
    LoansPeripheralContract,
    LiquidationsCoreContract,
    LiquidationsPeripheralContract,
    LiquidityControlsContract,
)

ENV = Environment[os.environ.get("ENV", "local")]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def load_contracts(env: Environment) -> set[ContractConfig]:
    config_file = f"{Path.cwd()}/configs/{env.name}/contracts.json"
    with open(config_file, "r") as f:
        config = json.load(f)["tokens"]["WETH"]

    def load(contract: ContractConfig):
        address = config.get(contract.config_key(), {}).get('contract', None)
        if address and env != Environment.local:
            contract.contract = contract.container.at(address)
        return contract

    return [load(c) for c in [
        LendingPoolCoreContract(None),
        LendingPoolPeripheralContract(None),
        CollateralVaultCoreContract(None),
        CollateralVaultPeripheralContract(None),
        LoansCoreContract(None),
        LoansPeripheralContract(None),
        LiquidationsCoreContract(None),
        LiquidationsPeripheralContract(None),
        LiquidityControlsContract(None),
        Token("weth", "token", None),
    ]]


def store_contracts(env: Environment, contracts: list[ContractConfig]):
    config_file = f"{Path.cwd()}/configs/{env.name}/contracts.json"
    file_struct = {'tokens': {'WETH': {c.config_key(): {'contract': c.address()} for c in contracts}}}
    with open(config_file, "w") as f:
        f.write(json.dumps(file_struct, indent=4, sort_keys=True))


def load_nft_contracts(env: Environment) -> list[NFT]:
    config_file = f"{Path.cwd()}/configs/{env.name}/nfts.json"
    with open(config_file, "r") as f:
        contracts = json.load(f)

    def load(name, pos):
        if env != Environment.local:
            return NFT(name, ERC721.at(contracts[pos]["contract"]), pos)
        else:
            return NFT(name, None, pos)

    return [
        load("cool_cats", 0),
        load("hashmasks", 1),
        load("bakc", 2),
        load("doodles", 3),
        load("wow", 4),
        load("mayc", 5),
        load("veefriends", 6),
        load("pudgy_penguins", 7),
        load("bayc", 8),
        load("wpunks", 9),
        NFT(
            "punks",
            ERC721.at('0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB') if env == Environment.prod else None,
            10
        ),
        # load("punks", 10),
        # NFT("newnft", ERC721.at(some_addr), 11),
    ]


def store_nft_contracts(env: Environment, nfts: list[NFT]):
    config_file = f"{Path.cwd()}/configs/{env.name}/nfts.json"
    sorted_nfts = sorted(nfts, key=lambda nft: nft.config_order)
    file_struct = [{'contract': nft.address()} for nft in sorted_nfts]

    with open(config_file, "w") as f:
        f.write(json.dumps(file_struct, indent=4))


def load_borrowable_amounts(env: Environment) -> dict:
    config_file = f"{Path.cwd()}/configs/{env.name}/collaterals_borrowable_amounts.json"
    with open(config_file, "r") as f:
        values = json.load(f)

    return {
        "cool_cats": values["cool_cats"],
        "hashmasks": values["hashmasks"],
        "bakc": values["bakc"],
        "doodles": values["doodles"],
        "wow": values["wow"],
        "mayc": values["mayc"],
        "veefriends": values["veefriends"],
        "pudgy_penguins": values["pudgy_penguins"],
        "bayc": values["bayc"],
        "wpunks": values["wpunks"],
        "punks": values["punks"],
    }


class DeploymentManager:
    def __init__(self, env: Environment):

        self.env = env
        match env:
            case Environment.local:
                self.owner = accounts[0]
            case Environment.dev:
                self.owner = accounts[0]
            case Environment.int:
                self.owner = accounts.load("goerliacc")
            case Environment.prod:
                self.owner = accounts.load("prodacc")

        self.context = DeploymentContext(self._get_contracts(), self.env, self.owner, self._get_configs())

    def _get_contracts(self) -> dict[str, ContractConfig]:
        contracts = load_contracts(self.env)
        nfts = load_nft_contracts(self.env)
        other = [
            GenericExternalContract("nftxvaultfactory", "0xBE86f647b167567525cCAAfcd6f881F1Ee558216"),
            GenericExternalContract("nftxmarketplacezap", "0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d"),
            GenericExternalContract("sushirouter", "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"),
        ]
        return {c.name: c for c in nfts + contracts + other}

    def _get_configs(self) -> dict[str, Any]:
        nft_borrowable_amounts = load_borrowable_amounts(self.env)
        return {"nft_borrowable_amounts": nft_borrowable_amounts}

    def _save_state(self):
        nft_contracts = [c for c in self.context.contract.values() if c.nft]
        contracts = [c for c in self.context.contract.values() if isinstance(c, InternalContract) or isinstance(c, Token)]
        store_nft_contracts(self.env, nft_contracts)
        store_contracts(self.env, contracts)

    def deploy(self, changes: set[str], dryrun=False, save_state=True):
        dependency_manager = DependencyManager(self.context, changes)
        contracts_to_deploy = dependency_manager.build_contract_deploy_set()
        dependencies_tx = dependency_manager.build_transaction_set()

        for contract in contracts_to_deploy:
            if contract.deployable(self.context):
                contract.deploy(self.context, dryrun)

        for dependency_tx in dependencies_tx:
            dependency_tx(self.context, dryrun)

        if save_state and not dryrun:
            self._save_state()

    def deploy_all(self, dryrun=False, save_state=True):
        self.deploy(self.context.contract.keys(), dryrun=dryrun, save_state=save_state)


def main():
    dm = DeploymentManager(ENV)
    dm.deploy({"collateral_vault_peripheral", "liquidations_peripheral", "loans"}, dryrun=True)
    # dm.deploy({"nft_borrowable_amounts"}, save_state=False)
    # dm.deploy({"loans", "liquidity_controls"}, dryrun=True)
    # dm.deploy_all(dryrun=False)
    pass
