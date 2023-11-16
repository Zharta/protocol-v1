import json
import logging
import warnings
import os

from typing import Any
from ape import accounts
from pathlib import Path
from operator import itemgetter
from itertools import groupby

from .dependency import DependencyManager
from .basetypes import (
    ContractConfig,
    DeploymentContext,
    Environment,
    GenericExternalContract,
    InternalContract,
    NFT,
)
from .contracts import (
    CollateralVaultCoreV2Contract,
    CollateralVaultOTCContract,
    CollateralVaultOTCImplContract,
    CollateralVaultPeripheralContract,
    CryptoPunksMockContract,
    CryptoPunksVaultCoreContract,
    DelegationRegistryMockContract,
    GenesisContract,
    LendingPoolCoreContract,
    LendingPoolLockContract,
    LendingPoolOTCContract,
    LendingPoolEthOTCImplContract,
    LendingPoolERC20OTCImplContract,
    LendingPoolPeripheralContract,
    LiquidationsCoreContract,
    LiquidationsPeripheralContract,
    LiquidationsOTCContract,
    LiquidationsOTCImplContract,
    LiquidityControlsContract,
    LoansCoreContract,
    LoansOTCContract,
    LoansOTCImplContract,
    LoansPeripheralContract,
    USDCMockContract,
    WETH9MockContract,
)

ENV = Environment[os.environ.get("ENV", "local")]

if ENV == Environment.dev:
    POOLS = ["weth", "usdc", "eth-grails", "eth-meta4", "swimming", "deadpool"]
elif ENV == Environment.int:
    POOLS = ["weth", "usdc", "eth-grails", "eth-meta4", "swimming", "usdc-tailored1"]
else:
    POOLS = ["weth", "usdc", "eth-grails", "eth-meta4", "usdc-rudolph"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
warnings.filterwarnings("ignore")


def contract_instances(env: Environment) -> dict:
    contracts = [
        WETH9MockContract(scope="weth", pools=["weth", "eth-grails", "swimming", "eth-meta4"]),
        USDCMockContract(scope="usdc", pools=["usdc", "deadpool", "usdc-tailored1", "usdc-rudolph"]),
        GenesisContract(pools=POOLS),
        DelegationRegistryMockContract(pools=POOLS),

        ## Shared
        CollateralVaultCoreV2Contract(scope=None, pools=["weth", "usdc"]),
        CollateralVaultPeripheralContract(scope=None, pools=["weth", "usdc"]),
        CryptoPunksVaultCoreContract(scope=None, pools=["weth", "usdc"]),
        LiquidationsCoreContract(scope=None, pools=["weth", "usdc"]),
        LiquidationsPeripheralContract(scope=None, pools=["weth", "usdc"]),

        ## WETH
        LendingPoolPeripheralContract(scope="weth", pools=["weth"]),
        LendingPoolCoreContract(scope="weth", pools=["weth"]),
        LendingPoolLockContract(scope="weth", pools=["weth"]),
        LiquidityControlsContract(scope="weth", pools=["weth"]),
        LoansPeripheralContract(scope="weth", pools=["weth"]),
        LoansCoreContract(scope="weth", pools=["weth"]),

        ## USDC
        LendingPoolPeripheralContract(scope="usdc", pools=["usdc"]),
        LendingPoolCoreContract(scope="usdc", pools=["usdc"]),
        LendingPoolLockContract(scope="usdc", pools=["usdc"]),
        LiquidityControlsContract(scope="usdc", pools=["usdc"]),
        LoansPeripheralContract(scope="usdc", pools=["usdc"]),
        LoansCoreContract(scope="usdc", pools=["usdc"]),

        ## Grails
        CollateralVaultCoreV2Contract(scope="eth-grails", pools=["eth-grails"]),
        CollateralVaultPeripheralContract(scope="eth-grails", pools=["eth-grails"]),
        CryptoPunksVaultCoreContract(scope="eth-grails", pools=["eth-grails"]),
        LendingPoolPeripheralContract(scope="eth-grails", pools=["eth-grails"]),
        LendingPoolCoreContract(scope="eth-grails", pools=["eth-grails"]),
        LendingPoolLockContract(scope="eth-grails", pools=["eth-grails"]),
        LiquidationsCoreContract(scope="eth-grails", pools=["eth-grails"]),
        LiquidationsPeripheralContract(scope="eth-grails", pools=["eth-grails"]),
        LiquidityControlsContract(scope="eth-grails", pools=["eth-grails"]),
        LoansPeripheralContract(scope="eth-grails", pools=["eth-grails"]),
        LoansCoreContract(scope="eth-grails", pools=["eth-grails"]),

        ## Proxy Implementations
        LendingPoolEthOTCImplContract(),
        LendingPoolERC20OTCImplContract(token="usdc", token_scope="usdc"),
        CollateralVaultOTCImplContract(),
        LoansOTCImplContract(),
        LiquidationsOTCImplContract(),

        ## ETH-META4
        CollateralVaultOTCContract(scope="eth-meta4", pools=["eth-meta4"]),
        LendingPoolOTCContract(impl="lending_pool_eth_otc_impl", scope="eth-meta4", pools=["eth-meta4"]),
        LiquidationsOTCContract(scope="eth-meta4", pools=["eth-meta4"]),
        LoansOTCContract(scope="eth-meta4", pools=["eth-meta4"]),

        ## USDC-RUDOLPH
        CollateralVaultOTCContract(scope="usdc-rudolph", pools=["usdc-rudolph"]),
        LendingPoolOTCContract(impl="lending_pool_usdc_otc_impl", scope="usdc-rudolph", pools=["usdc-rudolph"]),
        LiquidationsOTCContract(scope="usdc-rudolph", pools=["usdc-rudolph"]),
        LoansOTCContract(scope="usdc-rudolph", pools=["usdc-rudolph"]),
    ]

    if "swimming" in POOLS:
        contracts += [

            ## Swimming
            CollateralVaultOTCContract(scope="swimming", pools=["swimming"]),
            LendingPoolOTCContract(impl="lending_pool_eth_otc_impl", scope="swimming", pools=["swimming"]),
            LiquidationsOTCContract(scope="swimming", pools=["swimming"]),
            LoansOTCContract(scope="swimming", pools=["swimming"]),
        ]

    if "deadpool" in POOLS:
        contracts += [

            ## Deadpool
            CollateralVaultOTCContract(scope="deadpool", pools=["deadpool"]),
            LendingPoolOTCContract(impl="lending_pool_usdc_otc_impl", scope="deadpool", pools=["deadpool"]),
            LiquidationsOTCContract(scope="deadpool", pools=["deadpool"]),
            LoansOTCContract(scope="deadpool", pools=["deadpool"]),
        ]
    return {c.key(): c for c in contracts}


def load_contracts(env: Environment) -> list[ContractConfig]:
    contracts = contract_instances(env)

    config_file = f"{Path.cwd()}/configs/{env.name}/pools.json"
    with open(config_file, "r") as f:
        config = json.load(f)
    contract_configs = [c for pool_id, pool in config["pools"].items() for c in pool["contracts"].values()] + list(config["other"].values())
    addresses = {c["key"]: c["contract"] for c in contract_configs if c["contract"]}

    if env != Environment.local:
        for k, address in addresses.items():
            c = contracts[k]
            c.contract = c.container.at(address)

    return list(contracts.values())


def store_contracts(env: Environment, contracts: list[ContractConfig]):
    config_file = f"{Path.cwd()}/configs/{env.name}/pools.json"
    with open(config_file, "r") as f:
        config = json.load(f)

    contracts_dict = {c.key(): c for c in contracts}
    contract_configs = [c for pool_id, pool in config["pools"].items() for c in pool["contracts"].values()] + list(config["other"].values())
    for c in contract_configs:
        k = c["key"]
        if k in contracts_dict:
            c["contract"] = contracts_dict[k].address()
            c["contract_def"] = contracts_dict[k].container_name

    with open(config_file, "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))


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
        NFT("anticyclone", None),
        NFT("archetype", None),
        NFT("autoglyphs", None),
        NFT("azuki", None),
        NFT("bakc", None),
        NFT("bayc", None),
        NFT("beanz", None),
        NFT("chromie", None),
        NFT("clonex", None),
        NFT("cool", None),
        NFT("degods", None),
        NFT("doodles", None),
        NFT("fidenza", None),
        NFT("gazers", None),
        NFT("gundead", None),
        NFT("hm", None),
        NFT("hvmtl", None),
        NFT("invsble", None),
        NFT("lilpudgys", None),
        NFT("mayc", None),
        NFT("meebits", None),
        NFT("memoriesofqilin", None),
        NFT("meridian", None),
        NFT("miladymaker", None),
        NFT("moonbirds", None),
        NFT("oldquirkies", None),
        NFT("opepen", None),
        NFT("otherdeed", None),
        NFT("otherdeedexpanded", None),
        NFT("otherdeedkoda", None),
        NFT("othersidekoda", None),
        NFT("othersidemara", None),
        NFT("ppg", None),
        CryptoPunksMockContract(None) if env != Environment.prod else NFT("punk", None),
        NFT("quirkies", None),
        NFT("rektguy", None),
        NFT("renga", None),
        NFT("ringers", None),
        NFT("spaceriders", None),
        NFT("thecaptainz", None),
        NFT("thecurrency", None),
        NFT("theharvest", None),
        NFT("theeternalpump", None),
        NFT("theplague", None),
        NFT("thepotatoz", None),
        NFT("vft", None),
        NFT("wgame", None),
        NFT("wgamefarmer", None),
        NFT("wgameland", None),
        NFT("windsofyawanawa", None),
        NFT("wow", None),
        NFT("wpunk", None),
    ]]


def store_nft_contracts(env: Environment, nfts: list[NFT]):
    config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
    with open(config_file, "r") as f:
        file_data = json.load(f)

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
    limit_for_pool = lambda c, pool: c.get("conditions", {}).get(pool.upper(), {}).get("debt_limit", 0)

    collections = [v | {"collection_key": k} for k, v in values.items()]
    amounts = dict()
    for pool in POOLS:
        limit = lambda c: limit_for_pool(c, pool)
        max_collection_per_contract = [max(v, key=limit) for k, v in groupby(sorted(collections, key=address), address)]
        amounts |= {(pool, collection_key(c)): limit(c) for c in max_collection_per_contract}
    return amounts


class DeploymentManager:
    def __init__(self, env: Environment):

        self.env = env
        match env:
            case Environment.local:
                self.owner = accounts[0]
            case Environment.dev:
                self.owner = accounts.load("devacc")
            case Environment.int:
                self.owner = accounts.load("intacc")
            case Environment.prod:
                self.owner = accounts.load("prodacc")

        self.context = DeploymentContext(self._get_contracts(), self.env, self.owner, POOLS, self._get_configs())

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
        max_penalty_fees = {
            "weth": 2 * 10**17,
            "usdc": 300 * 10**6,
        }
        return {
            "nft_borrowable_amounts": nft_borrowable_amounts,
            "max_penalty_fees": max_penalty_fees,
            "genesis_owner": "0xd5312E8755B4E130b6CBF8edC3930757D6428De6" if self.env == Environment.prod else self.owner,
            "lpp_whitelist_enabled.eth-grails": True,
            "lpp_protocol_wallet_fees.weth": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            "lpp_protocol_wallet_fees.usdc": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            "lpp_protocol_wallet_fees.eth-grails": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            "lpp_protocol_wallet_fees.eth-meta4": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            "lpp_protocol_wallet_fees.usdc-rudolph": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            "lpp_protocol_fees_share.weth": 0,
            "lpp_protocol_fees_share.usdc": 0,
            "lpp_protocol_fees_share.eth-grails": 0,
            "lpp_protocol_fees_share.usdc-rudolph": 500,
            "lpp_max_capital_efficiency.weth": 8000,
            "lpp_max_capital_efficiency.usdc": 8000,
            "lpp_max_capital_efficiency.eth-grails": 10000,
            "lpp_max_capital_efficiency.usdc-rudolph": 10000,
            "loansperipheral_ispayable.weth": True,
            "loansperipheral_ispayable.usdc": False,
            "loansperipheral_ispayable.swimming": True,
            "loansperipheral_ispayable.deadpool": False,
            "loansperipheral_ispayable.eth-grails": True,
            "loansperipheral_ispayable.eth-meta4": True,
            "loansperipheral_ispayable.usdc-rudolph": False,
            "lender.swimming": "0x72651bb532a1feD9bb82266469242986ef5a70A3",
            "lender.deadpool": "0x72651bb532a1feD9bb82266469242986ef5a70A3",
            "lender.eth-meta4": "0x37B6a8fDee08Fe2F0aeAfDcf70DFC6ee842E27a9" if self.env == Environment.prod else self.owner,
            "lender.usdc-rudolph": "0x4d1572Ea399cfcb0a4b25B364dF2c5ba68697e18" if self.env == Environment.prod else self.owner,
        }

    def _save_state(self):
        nft_contracts = [c for c in self.context.contract.values() if c.nft]
        contracts = [c for c in self.context.contract.values() if isinstance(c, InternalContract)]
        store_nft_contracts(self.env, nft_contracts)
        store_contracts(self.env, contracts)

    def deploy(self, changes: set[str], dryrun=False, save_state=True):
        self.owner.set_autosign(True)
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
