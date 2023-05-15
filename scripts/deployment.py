import json
import logging
import warnings
import os

from typing import Any
from brownie import ERC721, accounts, chain
from pathlib import Path
from operator import itemgetter
from itertools import groupby

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
    CollateralVaultCoreV2Contract,
    CollateralVaultPeripheralContract,
    CryptoPunksMockContract,
    CryptoPunksVaultCoreContract,
    DelegationRegistryMockContract,
    GenesisContract,
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
TOKENS = ["weth", "usdc"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
warnings.filterwarnings("ignore")


def load_contracts(env: Environment) -> set[ContractConfig]:
    config_file = f"{Path.cwd()}/configs/{env.name}/contracts.json"
    with open(config_file, "r") as f:
        config = json.load(f)["tokens"]

    def load(contract: ContractConfig, token: str):
        address = config[token].get(contract.config_key(), {}).get('contract', None)
        if address and env != Environment.local:
            contract.contract = contract.container.at(address)
        return contract

    return [load(c, token.upper()) for token in TOKENS for c in [
        LendingPoolCoreContract(scope=token),
        LendingPoolLockContract(scope=token),
        LendingPoolPeripheralContract(scope=token),
        CollateralVaultCoreV2Contract(scope=token),
        CollateralVaultPeripheralContract(scope=token),
        CryptoPunksVaultCoreContract(scope=token),
        GenesisContract(),
        LoansCoreContract(scope=token),
        LoansPeripheralContract(scope=token),
        LiquidationsCoreContract(),
        LiquidationsPeripheralContract(scopes=TOKENS),
        LiquidityControlsContract(scope=token),
        WETH9MockContract(scope=token) if env != Environment.prod else Token("weth", "token", None),
        DelegationRegistryMockContract(),
    ]]


def store_contracts(env: Environment, contracts: list[ContractConfig]):
    config_file = f"{Path.cwd()}/configs/{env.name}/contracts.json"
    file_struct = {
        'tokens': {
            token.upper(): {
                c.config_key(): {'contract': c.address()} for c in contracts if not c.nft and not c.scope or c.scope == token
            } for token in TOKENS
        }
    }
    with open(config_file, "w") as f:
        f.write(json.dumps(file_struct, indent=4, sort_keys=True))


def load_nft_contracts(env: Environment) -> list[NFT]:
    config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
    with open(config_file, "r") as f:
        contracts = json.load(f)

    def load(contract: ContractConfig) -> ContractConfig:
        address = contracts.get(contract.config_key(), {}).get("contract_address", None)
        if address and env != Environment.local:
            contract.contract = contract.container.at(address)
        return contract

    return [load(c) for c in [
        NFT("cool", None),
        NFT("hm", None),
        NFT("bakc", None),
        NFT("doodles", None),
        NFT("wow", None),
        NFT("mayc", None),
        NFT("vft", None),
        NFT("ppg", None),
        NFT("bayc", None),
        NFT("wpunk", None),
        CryptoPunksMockContract(None) if env != Environment.prod else NFT("punk", None),
        NFT("chromie", None),
        NFT("ringers", None),
        NFT("gazers", None),
        NFT("fidenza", None),
        NFT("azuki", None),
        NFT("otherdeed", None),
        NFT("moonbirds", None),
        NFT("clonex", None),
        NFT("meebits", None),
        NFT("beanz", None),
        NFT("lilpudgys", None),
        NFT("gundead", None),
        NFT("invsble", None),
        NFT("quirkies", None),
        NFT("rektguy", None),
        NFT("renga", None),
        NFT("spaceriders", None),
        NFT("theplague", None),
        NFT("wgame", None),
        NFT("wgamefarmer", None),
        NFT("wgameland", None),
        NFT("otherdeedkoda", None),
        NFT("degods", None),
        NFT("othersidekoda", None),
        NFT("otherdeedexpanded", None),
        NFT("oldquirkies", None),
    ]]


def store_nft_contracts(env: Environment, nfts: list[NFT]):
    config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
    with open(config_file, "r") as f:
        file_data = json.load(f)

    # write_data = {nft.config_key(): file_data.get(nft.config_key(), {}) | {"contract_address": nft.address()} for nft in nfts}
    for nft in nfts:
        key = nft.config_key()
        if key in file_data:
            file_data[key]["contract_address"] = nft.address()
        else:
            file_data[key] = {"contract_address": nft.address()}

    with open(config_file, "w") as f:
        f.write(json.dumps(file_data, indent=2, sort_keys=True))


def load_borrowable_amounts(env: Environment) -> dict:
    config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
    with open(config_file, "r") as f:
        values = json.load(f)

    address = itemgetter("contract_address")
    collection_key = itemgetter("collection_key")
    limit = itemgetter("debt_limit")

    collections = [v | {"collection_key": k} for k, v in values.items()]
    max_collection_per_contract = [max(v, key=limit) for k, v in groupby(sorted(collections, key=address), address)]
    return {collection_key(c): limit(c) for c in max_collection_per_contract}


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
        return {c.key(): c for c in nfts + contracts + other}

    def _get_configs(self) -> dict[str, Any]:
        nft_borrowable_amounts = load_borrowable_amounts(self.env)
        # TODO fix when new collections format is ready
        return {
            "weth.nft_borrowable_amounts": nft_borrowable_amounts,
            "usdc.nft_borrowable_amounts": nft_borrowable_amounts,
            "genesis_owner": "0xd5312E8755B4E130b6CBF8edC3930757D6428De6" if self.env == Environment.prod else self.owner
        }

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
    changes |= {"nft_borrowable_amounts"}
    dm.deploy(changes, dryrun=True)

    for k, v in dm.context.contract.items():
        globals()[k.replace(".", "_")] = v.contract
        print(k.replace(".", "_"),v.contract)
    for k, v in dm.context.config.items():
        globals()[k.replace(".", "_")] = v

def console():
    dm = DeploymentManager(ENV)
    for k, v in dm.context.contract.items():
        globals()[k.replace(".", "_")] = v.contract
        print(k.replace(".", "_"),v.contract)
    for k, v in dm.context.config.items():
        globals()[k.replace(".", "_")] = v
