import json
import logging
import os

from brownie import (
    Contract,
    ERC20,
    ERC721,
    LendingPoolCore,
    LendingPoolPeripheral,
    CollateralVaultCore,
    CollateralVaultPeripheral,
    LoansCore,
    Loans,
    LiquidationsCore,
    LiquidationsPeripheral,
    LiquidityControls,
    web3,
    accounts,
)
from pathlib import Path
from .helpers.transactions import DependencyManager, Transaction


ENV = os.environ.get("ENV", "dev")

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

NAME_TO_CONTRACT = {
    "lending_pool_core": LendingPoolCore,
    "lending_pool": LendingPoolPeripheral,
    "collateral_vault_core": CollateralVaultCore,
    "collateral_vault_peripheral": CollateralVaultPeripheral,
    "loans_core": LoansCore,
    "loans": Loans,
    "liquidations_core": LiquidationsCore,
    "liquidations_peripheral": LiquidationsPeripheral,
    "liquidity_controls": LiquidityControls,
    "token": ERC20,
}

CONTRACT_DEPLOYMENT_ORDER = [
    "lending_pool_core",
    "lending_pool",
    "collateral_vault_core",
    "collateral_vault_peripheral",
    "loans_core",
    "loans",
    "liquidations_core",
    "liquidations_peripheral",
    "liquidity_controls",
]

CONTRACT_DEPLOYMENT_ARGS = {
    "collateral_vault_core": [],
    "collateral_vault_peripheral": [],
}


def load_contracts(env: str) -> dict:
    config_file = f"{Path.cwd()}/configs/{env}/contracts.json"
    with open(config_file, "r") as f:
        contracts = json.load(f)["tokens"]["WETH"]

    return {
        key: NAME_TO_CONTRACT[key].at(contracts[key]["contract"]) for key in contracts
    }


def load_nft_contracts(env: str) -> dict:
    config_file = f"{Path.cwd()}/configs/{env}/nfts.json"
    with open(config_file, "r") as f:
        contracts = json.load(f)

    return {
        "cool_cats": ERC721.at(contracts[0]["contract"]),
        "hashmasks": ERC721.at(contracts[1]["contract"]),
        "bakc": ERC721.at(contracts[2]["contract"]),
        "doodles": ERC721.at(contracts[3]["contract"]),
        "wow": ERC721.at(contracts[4]["contract"]),
        "mayc": ERC721.at(contracts[5]["contract"]),
        "veefriends": ERC721.at(contracts[6]["contract"]),
        "pudgy_penguins": ERC721.at(contracts[7]["contract"]),
        "bayc": ERC721.at(contracts[8]["contract"]),
        "wpunks": ERC721.at(contracts[9]["contract"]),
    }


def load_borrowable_amounts(env: str) -> dict:
    config_file = f"{Path.cwd()}/configs/{env}/collaterals_borrowable_amounts.json"
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
    def __init__(self, contract_names: list, env: str):
        aux_contract_order = []
        for contract_name in contract_names:
            idx = CONTRACT_DEPLOYMENT_ORDER.index(contract_name)
            aux_contract_order.append([contract_name, idx])
        aux_contract_order.sort(key=lambda k: k[1], reverse=False)
        self.contract_names = list(map(lambda k: k[0], aux_contract_order))

        if env not in ["local", "dev", "int", "prod"]:
            raise ValueError("'env' value is not in ['dev', 'int', 'prod']")
        self.env = env

        match env:
            case "local":
                self.owner = accounts[0]
            case "dev":
                self.owner = accounts[0]
            case "int":
                self.owner = accounts.load("goerliacc")
            case "prod":
                self.owner = accounts.load("prodacc")
            case _:
                self.owner = None

    def _get_deploy_args(self, contract_name: str, contracts: dict):
        match contract_name:
            case "collateral_vault_core":
                return [{"from": self.owner}]
            case "collateral_vault_peripheral":
                return [contracts["collateral_vault_core"], {"from": self.owner}]
            case "lending_pool_core":
                return [contracts["token"], {"from": self.owner}]
            case "lending_pool":
                return [
                    contracts["lending_pool_core"],
                    contracts["token"],
                    self.owner,
                    2500,
                    7000,
                    False,
                    {"from": self.owner},
                ]
            case "loans_core":
                return [{"from": self.owner}]
            case "loans":
                return [
                    1000000,
                    31 * 86400,
                    web3.toWei(10000, "ether"),
                    24 * 60 * 60,
                    contracts["loans_core"],
                    contracts["lending_pool"],
                    contracts["collateral_vault_peripheral"],
                    {"from": self.owner},
                ]
            case "liquidations_core":
                return [{"from": self.owner}]
            case "liquidations_peripheral":
                return [
                    contracts["liquidations_core"],
                    2 * 86400,
                    2 * 86400,
                    2 * 86400,
                    contracts["token"],
                    {"from": self.owner},
                ]
            case "liquidity_controls":
                return [
                    False,
                    1500,
                    False,
                    7 * 24 * 60 * 60,
                    False,
                    1500,
                    False,
                    {"from": self.owner},
                ]
            case _:
                return []

    def _deploy_contract(self, contract_name: str, contracts: dict) -> Contract:
        deploy_args = self._get_deploy_args(contract_name, contracts)
        logger.warning(f"\n\n{contract_name} deploy args -> {deploy_args}")

        contract = NAME_TO_CONTRACT[contract_name].deploy(*deploy_args)
        return contract

    def _get_tx_args(
        self,
        transaction: Transaction,
        contracts: dict,
        nft_contracts: list,
        borrowable_amounts: list,
    ):
        match transaction:
            case Transaction.lpcore_set_lpperiph:
                result = [
                    contracts["lending_pool_core"],
                    contracts["lending_pool"],
                ]
            case Transaction.lpperiph_set_loansperiph:
                result = [contracts["lending_pool"], contracts["loans"]]
            case Transaction.lpperiph_set_liquidationsperiph:
                result = [
                    contracts["lending_pool"],
                    contracts["liquidations_peripheral"],
                ]
            case Transaction.lpperiph_set_liquiditycontrols:
                result = [
                    contracts["lending_pool"],
                    contracts["liquidations_core"],
                ]
            case Transaction.cvcore_set_cvperiph:
                result = [
                    contracts["collateral_vault_core"],
                    contracts["collateral_vault_peripheral"],
                ]
            case Transaction.cvperiph_add_loansperiph:
                result = [
                    contracts["collateral_vault_peripheral"],
                    contracts["token"],
                    contracts["loans"],
                ]
            case Transaction.cvperiph_set_liquidationsperiph:
                result = [
                    contracts["collateral_vault_peripheral"],
                    contracts["liquidations_peripheral"],
                ]
            case Transaction.loanscore_set_loansperiph:
                result = [contracts["loans_core"], contracts["loans"]]
            case Transaction.loansperiph_set_liquidationsperiph:
                result = [
                    contracts["loans"],
                    contracts["liquidations_peripheral"],
                ]
            case Transaction.loansperiph_set_liquiditycontrols:
                result = [
                    contracts["loans"],
                    contracts["liquidity_controls"],
                ]
            case Transaction.loansperiph_set_lpperiph:
                result = [contracts["loans"], contracts["lending_pool"]]
            case Transaction.loansperiph_set_cvperiph:
                result = [
                    contracts["loans"],
                    contracts["collateral_vault_peripheral"],
                ]
            case Transaction.liquidationscore_set_liquidationsperiph:
                result = [
                    contracts["liquidations_core"],
                    contracts["liquidations_peripheral"],
                ]
            case Transaction.liquidationscore_add_loanscore:
                result = [
                    contracts["liquidations_core"],
                    contracts["token"],
                    contracts["loans_core"],
                ]
            case Transaction.liquidationsperiph_set_liquidationscore:
                result = [
                    contracts["liquidations_peripheral"],
                    contracts["liquidations_core"],
                ]
            case Transaction.liquidationsperiph_add_loanscore:
                result = [
                    contracts["liquidations_peripheral"],
                    contracts["token"],
                    contracts["loans_core"],
                ]
            case Transaction.liquidationsperiph_add_lpperiph:
                result = [
                    contracts["liquidations_peripheral"],
                    contracts["token"],
                    contracts["lending_pool"],
                ]
            case Transaction.liquidationsperiph_set_cvperiph:
                result = [
                    contracts["liquidations_peripheral"],
                    contracts["collateral_vault_peripheral"],
                ]
            case Transaction.liquidationsperiph_set_nftxvaultfactory:
                result = [
                    contracts["liquidations_peripheral"],
                    "0xBE86f647b167567525cCAAfcd6f881F1Ee558216",
                ]
            case Transaction.liquidationsperiph_set_nftxmarketplacezap:
                result = [
                    contracts["liquidations_peripheral"],
                    "0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d",
                ]
            case Transaction.liquidationsperiph_set_sushirouter:
                result = [
                    contracts["liquidations_peripheral"],
                    "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
                ]
            case Transaction.loansperiph_add_collaterals:
                result = [contracts["loans"], nft_contracts]
            case Transaction.liquiditycontrols_change_collectionborrowableamounts:
                result = [
                    contracts["liquidity_controls"],
                    nft_contracts,
                    borrowable_amounts,
                ]
            case _:
                result = []

        result.append(self.owner)
        return result

    def _run_dependency_tx(
        self,
        dependency_tx: Transaction,
        contracts: dict,
        nft_contracts: list,
        borrowable_amounts: list,
    ):
        args = self._get_tx_args(
            dependency_tx, contracts, nft_contracts, borrowable_amounts
        )
        logger.warning(f"\n\nDEPENDENCY_TX -> {dependency_tx}")
        logger.warning(f"ARGS -> {args}")

        dependency_tx(*args)

    def _deploy_test_assets(self):
        if self.env == "prod":
            raise ValueError("'env' can not be prod to deploy test assets")

        ### TEST NFT CONTRACTS ###
        cool_cats_instance = ERC721.deploy({"from": self.owner})
        hashmasks_instance = ERC721.deploy({"from": self.owner})
        kennel_instance = ERC721.deploy({"from": self.owner})
        doodles_instance = ERC721.deploy({"from": self.owner})
        wow_instance = ERC721.deploy({"from": self.owner})
        mutant_instance = ERC721.deploy({"from": self.owner})
        veefriends_instance = ERC721.deploy({"from": self.owner})
        pudgypenguins_instance = ERC721.deploy({"from": self.owner})
        bayc_instance = ERC721.deploy({"from": self.owner})
        wpunks_instance = ERC721.deploy({"from": self.owner})

        ### TEST WETH CONTRACT ###
        weth = ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {"from": self.owner})

        return (
            cool_cats_instance,
            hashmasks_instance,
            kennel_instance,
            doodles_instance,
            wow_instance,
            mutant_instance,
            veefriends_instance,
            pudgypenguins_instance,
            bayc_instance,
            wpunks_instance,
            weth,
        )

    def _get_contracts(self, full_deployment=False):
        contracts = {}

        if self.env == "prod" or not full_deployment:
            nft_contracts = load_nft_contracts(self.env)
        elif self.env != "prod" and full_deployment:
            (
                cool_cats_instance,
                hashmasks_instance,
                kennel_instance,
                doodles_instance,
                wow_instance,
                mutant_instance,
                veefriends_instance,
                pudgypenguins_instance,
                bayc_instance,
                wpunks_instance,
                weth,
            ) = self._deploy_test_assets()

            nft_contracts = {}
            nft_contracts["cool_cats"] = cool_cats_instance
            nft_contracts["hashmasks"] = hashmasks_instance
            nft_contracts["bakc"] = kennel_instance
            nft_contracts["doodles"] = doodles_instance
            nft_contracts["wow"] = wow_instance
            nft_contracts["mayc"] = mutant_instance
            nft_contracts["veefriends"] = veefriends_instance
            nft_contracts["pudgy_penguins"] = pudgypenguins_instance
            nft_contracts["bayc"] = bayc_instance
            nft_contracts["wpunks"] = wpunks_instance

            contracts["token"] = weth

        if full_deployment:
            for name in NAME_TO_CONTRACT:
                if name == "token":
                    continue
                contracts[name] = self._deploy_contract(name, contracts)
        else:
            contracts = load_contracts(self.env)

        return contracts, nft_contracts

    def deploy(self, full_deployment=False):
        nft_borrowable_amounts = load_borrowable_amounts(self.env)
        contracts, nft_contracts = self._get_contracts(full_deployment)

        dependency_manager = DependencyManager(self.contract_names)
        dependencies_tx = dependency_manager.build_transaction_set()

        contracts_to_deploy = dependency_manager.build_contract_deploy_set()

        for contract in contracts_to_deploy:
            contracts[contract] = self._deploy_contract(contract, contracts)

        nft_contract_addresses = []
        borrowable_amounts = []
        for key in nft_contracts:
            nft_contract_addresses.append(nft_contracts[key])
            borrowable_amounts.append(nft_borrowable_amounts[key])

        for dependency_tx in dependencies_tx:
            self._run_dependency_tx(
                dependency_tx, contracts, nft_contract_addresses, borrowable_amounts
            )


def main():
    # DeploymentManager(["loans"], ENV).deploy(full_deployment=True)
    pass
