import json
import logging
import os
import warnings
from pathlib import Path
from typing import Any

from ape import accounts

from . import contracts as contracts_module
from .basetypes import (
    ContractConfig,
    DeploymentContext,
    Environment,
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
    LendingPoolERC20OTCImplContract,
    LendingPoolEthOTCImplContract,
    LendingPoolLockContract,
    LendingPoolOTCContract,
    LendingPoolPeripheralContract,
    LiquidationsCoreContract,
    LiquidationsOTCContract,
    LiquidationsOTCImplContract,
    LiquidationsPeripheralContract,
    LiquidityControlsContract,
    LoansCoreContract,
    LoansOTCContract,
    LoansOTCImplContract,
    LoansOTCPunksFixedContract,
    LoansOTCPunksFixedImplContract,
    LoansPeripheralContract,
    USDCMockContract,
    WETH9MockContract,
)
from .dependency import DependencyManager

ENV = Environment[os.environ.get("ENV", "local")]


def load_contracts(env: Environment) -> list[ContractConfig]:
    config_file = Path.cwd() / "configs" / env.name / "pools.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    contract_configs = {
        f"{pool_id.lower()}.{key}": c for pool_id, pool in config["pools"].items() for key, c in pool["contracts"].values()
    } | {f"common.{k}": v for k, v in config["common"].items()}

    return [
        contracts_module.__dict__[c["contract_def"]](
            key=key, address=c.get("contract"), abi_key=c.get("abi_key"), **c.get("properties", {})
        )
        for key, c in contract_configs.items()
    ]


def store_contracts(env: Environment, contracts: list[ContractConfig]):
    config_file = Path.cwd() / "configs" / env.name / "pools.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    contracts_dict = {c.key: c for c in contracts}

    contract_configs = {
        f"{pool_id.lower()}.{key}": c for pool_id, pool in config["pools"].items() for key, c in pool["contracts"].values()
    } | {f"common.{k}": v for k, v in config["common"].items()}

    for key, c in contract_configs.items():
        if key in contracts_dict:
            c["contract"] = contracts_dict[key].address()
            if contracts_dict[key].abi_key:
                c["abi_key"] = contracts_dict[key].abi_key
            if contracts_dict[key].version:
                c["version"] = contracts_dict[key].version
        properties = c.get("properties", {})
        addresses = c.get("properties_addresses", {})
        for prop_key, prop_val in properties.items():
            if prop_key.endswith("_key"):
                addresses[prop_key[:-4]] = contracts_dict[prop_val].address()
        c["properties_addresses"] = addresses

    with config_file.open(mode="w", encoding="utf8") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))


def load_nft_contracts(env: Environment) -> list[ContractConfig]:
    config_file = Path.cwd() / "configs" / env.name / "collections.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    return [
        contracts_module.__dict__[c.get("contract_def", "ERC721Contract")](
            key=key,
            address=c.get("contract_address"),
        )
        for key, c in config.items()
    ]


def store_nft_contracts(env: Environment, contracts: list[ContractConfig]):
    config_file = Path.cwd() / "configs" / env.name / "collections.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    contracts_dict = {c.key: c for c in contracts}

    for key, c in config.items():
        if key in contracts_dict:
            c["contract_address"] = contracts_dict[key].address()

    with config_file.open(mode="w", encoding="utf8") as f:
        f.write(json.dumps(config, indent=2, sort_keys=True))


def load_configs(env: Environment) -> dict:
    config_file = Path.cwd() / "configs" / env.name / "pools.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    return config.get("configs", {})


if ENV == Environment.dev:
    POOLS = ["weth", "usdc", "eth-grails", "swimming", "deadpool", "eth-meta4"]
elif ENV == Environment.int:
    POOLS = ["weth", "usdc", "eth-grails", "swimming", "usdc-tailored1", "eth-meta4"]
else:
    POOLS = ["weth", "usdc", "eth-grails", "eth-kashi", "eth-keyrock", "usdc-rudolph", "usdc-sgdao"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
warnings.filterwarnings("ignore")


def contract_instances(env: Environment) -> dict:
    contracts = [
        WETH9MockContract(scope="weth", pools=["weth", "eth-grails", "swimming", "eth-meta4", "eth-kashi", "eth-keyrock"]),
        USDCMockContract(scope="usdc", pools=["usdc", "deadpool", "usdc-tailored1", "usdc-sgdao"]),
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
        LoansOTCPunksFixedImplContract(),
        LiquidationsOTCImplContract(),
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

    if "usdc-tailored1" in POOLS:
        contracts += [
            ## USDC-TAILORED1
            CollateralVaultOTCContract(scope="usdc-tailored1", pools=["usdc-tailored1"]),
            LendingPoolOTCContract(impl="lending_pool_usdc_otc_impl", scope="usdc-tailored1", pools=["usdc-tailored1"]),
            LiquidationsOTCContract(scope="usdc-tailored1", pools=["usdc-tailored1"]),
            LoansOTCContract(scope="usdc-tailored1", pools=["usdc-tailored1"]),
        ]

    if "usdc-springboks" in POOLS:
        contracts += [
            ## USDC-SPRINGBOKS
            CollateralVaultOTCContract(scope="usdc-springboks", pools=["usdc-springboks"]),
            LendingPoolOTCContract(impl="lending_pool_usdc_otc_impl", scope="usdc-springboks", pools=["usdc-springboks"]),
            LiquidationsOTCContract(scope="usdc-springboks", pools=["usdc-springboks"]),
            LoansOTCPunksFixedContract(scope="usdc-springboks", pools=["usdc-springboks"]),
        ]

    if "eth-meta4" in POOLS:
        contracts += [
            ## ETH-META4
            CollateralVaultOTCContract(scope="eth-meta4", pools=["eth-meta4"]),
            LendingPoolOTCContract(impl="lending_pool_eth_otc_impl", scope="eth-meta4", pools=["eth-meta4"]),
            LiquidationsOTCContract(scope="eth-meta4", pools=["eth-meta4"]),
            LoansOTCContract(scope="eth-meta4", pools=["eth-meta4"]),
        ]

    if "eth-kashi" in POOLS:
        contracts += [
            ## ETH-KASHI
            CollateralVaultOTCContract(scope="eth-kashi", pools=["eth-kashi"]),
            LendingPoolOTCContract(impl="lending_pool_eth_otc_impl", scope="eth-kashi", pools=["eth-kashi"]),
            LiquidationsOTCContract(scope="eth-kashi", pools=["eth-kashi"]),
            LoansOTCContract(scope="eth-kashi", pools=["eth-kashi"]),
        ]

    if "eth-keyrock" in POOLS:
        contracts += [
            ## ETH-KEYROCK
            CollateralVaultOTCContract(scope="eth-keyrock", pools=["eth-keyrock"]),
            LendingPoolOTCContract(impl="lending_pool_eth_otc_impl", scope="eth-keyrock", pools=["eth-keyrock"]),
            LiquidationsOTCContract(scope="eth-keyrock", pools=["eth-keyrock"]),
            LoansOTCContract(scope="eth-keyrock", pools=["eth-keyrock"]),
        ]

    if "usdc-sgdao" in POOLS:
        contracts += [
            ## USDC-SGDAO
            CollateralVaultCoreV2Contract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            CollateralVaultPeripheralContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            CryptoPunksVaultCoreContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LiquidationsCoreContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LiquidationsPeripheralContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LendingPoolPeripheralContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LendingPoolCoreContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LendingPoolLockContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LiquidityControlsContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LoansPeripheralContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
            LoansCoreContract(scope="usdc-sgdao", pools=["usdc-sgdao"]),
        ]

    return {c.key(): c for c in contracts}


# def load_contracts(env: Environment) -> list[ContractConfig]:
#     contracts = contract_instances(env)

#     config_file = f"{Path.cwd()}/configs/{env.name}/pools.json"
#     with open(config_file, "r") as f:
#         config = json.load(f)
#     contract_configs = [c for pool_id, pool in config["pools"].items() for c in pool["contracts"].values()] + list(
#         config["other"].values()
#     )
#     addresses = {c["key"]: c["contract"] for c in contract_configs if c["contract"]}

#     if env != Environment.local:
#         for k, address in addresses.items():
#             c = contracts[k]
#             c.contract = c.container.at(address)

#     return list(contracts.values())


# def store_contracts(env: Environment, contracts: list[ContractConfig]):
#     config_file = f"{Path.cwd()}/configs/{env.name}/pools.json"
#     with open(config_file, "r") as f:
#         config = json.load(f)

#     contracts_dict = {c.key(): c for c in contracts}
#     contract_configs = [c for pool_id, pool in config["pools"].items() for c in pool["contracts"].values()] + list(
#         config["other"].values()
#     )
#     for c in contract_configs:
#         k = c["key"]
#         if k in contracts_dict:
#             c["contract"] = contracts_dict[k].address()
#             c["contract_def"] = contracts_dict[k].container_name

#     with open(config_file, "w") as f:
#         f.write(json.dumps(config, indent=4, sort_keys=True))


# def load_nft_contracts(env: Environment) -> list[NFT]:
#     config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
#     with open(config_file, "r") as f:
#         contracts = json.load(f)

#     def load(contract: ContractConfig) -> ContractConfig:
#         address = contracts.get(contract.config_key(), {}).get("contract_address", None)
#         if address and env != Environment.local:
#             contract.contract = contract.container.at(address)
#         return contract

#     return [
#         load(c)
#         for c in [
#             NFT("anticyclone", None),
#             NFT("archetype", None),
#             NFT("autoglyphs", None),
#             NFT("azuki", None),
#             NFT("bakc", None),
#             NFT("bayc", None),
#             NFT("beanz", None),
#             NFT("chromie", None),
#             NFT("clonex", None),
#             NFT("cool", None),
#             NFT("degods", None),
#             NFT("doodles", None),
#             NFT("fidenza", None),
#             NFT("gazers", None),
#             NFT("gundead", None),
#             NFT("hm", None),
#             NFT("hvmtl", None),
#             NFT("invsble", None),
#             NFT("lilpudgys", None),
#             NFT("mayc", None),
#             NFT("meebits", None),
#             NFT("memoriesofqilin", None),
#             NFT("meridian", None),
#             NFT("miladymaker", None),
#             NFT("moonbirds", None),
#             NFT("oldquirkies", None),
#             NFT("opepen", None),
#             NFT("otherdeed", None),
#             NFT("otherdeedexpanded", None),
#             NFT("otherdeedkoda", None),
#             NFT("othersidekoda", None),
#             NFT("othersidekodamara", None),
#             NFT("othersidemara", None),
#             NFT("ppg", None),
#             CryptoPunksMockContract(None) if env != Environment.prod else NFT("punk", None),
#             NFT("quirkies", None),
#             NFT("rektguy", None),
#             NFT("renga", None),
#             NFT("ringers", None),
#             NFT("spaceriders", None),
#             NFT("thecaptainz", None),
#             NFT("thecurrency", None),
#             NFT("theharvest", None),
#             NFT("theeternalpump", None),
#             NFT("theplague", None),
#             NFT("thepotatoz", None),
#             NFT("vft", None),
#             NFT("wgame", None),
#             NFT("wgamefarmer", None),
#             NFT("wgameland", None),
#             NFT("windsofyawanawa", None),
#             NFT("wow", None),
#             NFT("wpunk", None),
#         ]
#     ]


# def store_nft_contracts(env: Environment, nfts: list[NFT]):
#     config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
#     with open(config_file, "r") as f:
#         file_data = json.load(f)

#     for nft in nfts:
#         key = nft.config_key()
#         if key in file_data:
#             file_data[key]["contract_address"] = nft.address()
#         else:
#             file_data[key] = {"contract_address": nft.address()}

#     with open(config_file, "w") as f:
#         f.write(json.dumps(file_data, indent=2, sort_keys=True))


# def load_borrowable_amounts(env: Environment) -> dict:
#     config_file = f"{Path.cwd()}/configs/{env.name}/collections.json"
#     with open(config_file, "r") as f:
#         values = json.load(f)

#     address = itemgetter("contract_address")
#     collection_key = itemgetter("collection_key")
#     limit_for_pool = lambda c, pool: c.get("conditions", {}).get(pool.upper(), {}).get("debt_limit", 0)

#     collections = [v | {"collection_key": k} for k, v in values.items()]
#     amounts = dict()
#     for pool in POOLS:
#         limit = lambda c: limit_for_pool(c, pool)
#         max_collection_per_contract = [max(v, key=limit) for k, v in groupby(sorted(collections, key=address), address)]
#         amounts |= {(pool, collection_key(c)): limit(c) for c in max_collection_per_contract}
#     return amounts


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
            GenericContract(key="nftxvaultfactory", address="0xBE86f647b167567525cCAAfcd6f881F1Ee558216"),
            GenericContract(key="nftxmarketplacezap", address="0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d"),
            GenericContract(key="sushirouter", address="0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"),
        ]
        all_contracts = contracts + nfts + other

        # always deploy everything in local
        if self.env == Environment.local:
            for contract in all_contracts:
                contract.contract = None

        return {c.key(): c for c in all_contracts}

    def _get_configs(self) -> dict[str, Any]:
        # nft_borrowable_amounts = load_borrowable_amounts(self.env)

        return load_configs(self.env)

        max_penalty_fees = {
            "weth": 2 * 10**17,
            "usdc": 300 * 10**6,
            "usdc-sgdao": 300 * 10**6,
        }
        return {
            # "nft_borrowable_amounts": nft_borrowable_amounts,
            "max_penalty_fees": max_penalty_fees,
            "genesis_owner": "0xd5312E8755B4E130b6CBF8edC3930757D6428De6" if self.env == Environment.prod else self.owner,
            # WETH
            "lpp_protocol_wallet_fees.weth": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "lpp_protocol_fees_share.weth": 0,
            "lpp_max_capital_efficiency.weth": 8000,
            "loansperipheral_ispayable.weth": True,
            # USDC
            "lpp_protocol_wallet_fees.usdc": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "lpp_protocol_fees_share.usdc": 0,
            "lpp_max_capital_efficiency.usdc": 8000,
            "loansperipheral_ispayable.usdc": False,
            # ETH-GRAILS
            "lpp_whitelist_enabled.eth-grails": True,
            "lpp_protocol_wallet_fees.eth-grails": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "lpp_protocol_fees_share.eth-grails": 0,
            "lpp_max_capital_efficiency.eth-grails": 10000,
            "loansperipheral_ispayable.eth-grails": True,
            # ETH-KASHI
            "lpp_protocol_wallet_fees.eth-kashi": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "loansperipheral_ispayable.eth-kashi": True,
            "lender.eth-kashi": "0xDd3e9d0eE979E5c1689A18992647312b42d6d8F3" if self.env == Environment.prod else self.owner,
            # ETH-KEYROCK
            "lpp_protocol_wallet_fees.eth-keyrock": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "loansperipheral_ispayable.eth-keyrock": True,
            "lender.eth-keyrock": "0xf1a9676B03Dd3B2066214D2aD8B4B59ED6642C53" if self.env == Environment.prod else self.owner,
            # ETH-META4
            # "lpp_protocol_wallet_fees.eth-meta4": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            # "loansperipheral_ispayable.eth-meta4": True,
            # "lender.eth-meta4": "0x37B6a8fDee08Fe2F0aeAfDcf70DFC6ee842E27a9" if self.env == Environment.prod else self.owner,
            # USDC-RUDOLPH
            "lpp_protocol_wallet_fees.usdc-rudolph": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "lpp_protocol_fees_share.usdc-rudolph": 500,
            "lpp_max_capital_efficiency.usdc-rudolph": 10000,
            "loansperipheral_ispayable.usdc-rudolph": False,
            "lender.usdc-rudolph": "0x4d1572Ea399cfcb0a4b25B364dF2c5ba68697e18"
            if self.env == Environment.prod
            else self.owner,
            # USDC-SPRINGBOKS
            # "lpp_protocol_wallet_fees.usdc-springboks": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6" if self.env == Environment.prod else self.owner,
            # "lpp_protocol_fees_share.usdc-springboks": 500,
            # "lpp_max_capital_efficiency.usdc-springboks": 10000,
            # "loansperipheral_ispayable.usdc-springboks": False,
            # "lender.usdc-springboks": "0xd7Fc4Ab828AFc1bb4b217f337f1777Ca856Efd12" if self.env == Environment.prod else self.owner,
            # USDC-SGDAO
            "lpp_whitelist_enabled.usdc-sgdao": True,
            "lpp_protocol_wallet_fees.usdc-sgdao": "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6"
            if self.env == Environment.prod
            else self.owner,
            "lpp_protocol_fees_share.usdc-sgdao": 0,
            "lpp_max_capital_efficiency.usdc-sgdao": 10000,
            "loansperipheral_ispayable.usdc-sgdao": False,
            # SWIMMING, DEADPOOL
            "loansperipheral_ispayable.swimming": True,
            "loansperipheral_ispayable.deadpool": False,
            "lender.swimming": "0x72651bb532a1feD9bb82266469242986ef5a70A3",
            "lender.deadpool": "0x72651bb532a1feD9bb82266469242986ef5a70A3",
        }

    def _save_state(self):
        nft_contracts = [c for c in self.context.contract.values() if c.nft]
        contracts = [c for c in self.context.contract.values() if not c.nft]
        store_nft_contracts(self.env, nft_contracts)
        store_contracts(self.env, contracts)

    def deploy(self, changes: set[str], dryrun=False, save_state=True):
        self.owner.set_autosign(True)
        self.context.dryrun = dryrun
        dependency_manager = DependencyManager(self.context, changes)
        contracts_to_deploy = dependency_manager.build_contract_deploy_set()
        dependencies_tx = dependency_manager.build_transaction_set()

        for contract in contracts_to_deploy:
            if contract.deployable(self.context):
                contract.deploy(self.context)

        for dependency_tx in dependencies_tx:
            dependency_tx(self.context)

        if save_state and not dryrun:
            self._save_state()

    def deploy_all(self, dryrun=False, save_state=True):
        self.deploy(self.context.contract.keys(), dryrun=dryrun, save_state=save_state)
