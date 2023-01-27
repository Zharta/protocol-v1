import json
import logging
import os

from typing import Any
from brownie import ERC721, accounts, chain
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
    CollateralVaultCoreContract,
    CollateralVaultPeripheralContract,
    CryptoPunksMockContract,
    CryptoPunksVaultCoreContract,
    LendingPoolCoreContract,
    LendingPoolLockContract,
    LendingPoolPeripheralContract,
    LiquidationsCoreContract,
    LiquidationsPeripheralContract,
    LiquidityControlsContract,
    LoansCoreContract,
    LoansPeripheralContract,
    WETH9MockContract,
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
        LendingPoolLockContract(None),
        LendingPoolPeripheralContract(None),
        CollateralVaultCoreContract(None),
        CollateralVaultPeripheralContract(None),
        CryptoPunksVaultCoreContract(None),
        LoansCoreContract(None),
        LoansPeripheralContract(None),
        LiquidationsCoreContract(None),
        LiquidationsPeripheralContract(None),
        LiquidityControlsContract(None),
        WETH9MockContract(None) if env != Environment.prod else Token("weth", "token", None),
    ]]


def store_contracts(env: Environment, contracts: list[ContractConfig]):
    config_file = f"{Path.cwd()}/configs/{env.name}/contracts.json"
    file_struct = {
        'tokens': {
            'WETH': {
                c.config_key(): {'contract': c.address()} for c in contracts if not c.nft
            }
        }
    }
    with open(config_file, "w") as f:
        f.write(json.dumps(file_struct, indent=4, sort_keys=True))


NFT_STORE_ORDER = [
    "cool_cats",
    "hashmasks",
    "bakc",
    "doodles",
    "wow",
    "mayc",
    "veefriends",
    "pudgy_penguins",
    "bayc",
    "wpunks",
    "cryptopunks"
]

def load_nft_contracts(env: Environment) -> list[NFT]:
    config_file = f"{Path.cwd()}/configs/{env.name}/nfts.json"
    order_map = {v: i for i, v in enumerate(NFT_STORE_ORDER)}
    with open(config_file, "r") as f:
        contracts = json.load(f)

    def load(contract: ContractConfig) -> ContractConfig:
        idx = order_map[contract.config_key()]
        address = contracts[idx]["contract"]
        if address and env != Environment.local:
            contract.contract = contract.container.at(address)
        return contract

    return [load(c) for c in [
        NFT("cool_cats", None),
        NFT("hashmasks", None),
        NFT("bakc", None),
        NFT("doodles", None),
        NFT("wow", None),
        NFT("mayc", None),
        NFT("veefriends", None),
        NFT("pudgy_penguins", None),
        NFT("bayc", None),
        NFT("wpunks", None),
        CryptoPunksMockContract(None) if env != Environment.prod else NFT("cryptopunks", None),
    ]]


def store_nft_contracts(env: Environment, nfts: list[NFT]):
    config_file = f"{Path.cwd()}/configs/{env.name}/nfts.json"
    order_map = {v: i for i, v in enumerate(NFT_STORE_ORDER)}
    sorted_nfts = sorted(nfts, key=lambda nft: order_map[nft.config_key()])
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
        "cryptopunks": values["punks"],
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


def gas_cost(context):

    return {'gas_price': '32 gwei'}


def main():

    dm = DeploymentManager(ENV)
    dm.context.gas_func = gas_cost

    changes = set()
    dm.deploy(changes, dryrun=True)


def console():
    dm = DeploymentManager(ENV)
    cvp = dm.context["collateral_vault_peripheral"].contract
    cvc = dm.context["collateral_vault_core"].contract
    pvc = dm.context["cryptopunks_vault_core"].contract
    lpc = dm.context["lending_pool_core"].contract
    lpl = dm.context["lending_pool_lock"].contract
    lpp = dm.context["lending_pool_peripheral"].contract
    lp = dm.context["loans"].contract
    lc = dm.context["loans_core"].contract
    lic = dm.context["liquidations_core"].contract
    lip = dm.context["liquidations_peripheral"].contract
    ctrl = dm.context["liquidity_controls"].contract

    weth = dm.context["weth"].contract

    cats = dm.context["cool_cats"].contract
    masks = dm.context["hashmasks"].contract
    bakc = dm.context["bakc"].contract
    doodles = dm.context["doodles"].contract
    wow = dm.context["wow"].contract
    mayc = dm.context["mayc"].contract
    veefriends = dm.context["veefriends"].contract
    penguins = dm.context["pudgy_penguins"].contract
    bayc = dm.context["bayc"].contract
    wpunks = dm.context["wpunks"].contract
    punks = dm.context["cryptopunks"].contract
