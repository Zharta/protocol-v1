import logging
import json

from brownie import (
    accounts,
    ERC721,
    ERC20,
    LendingPoolCore,
    LendingPoolPeripheral,
    CollateralVaultCore,
    CryptoPunksVaultCore,
    CollateralVaultPeripheral,
    LoansCore,
    Loans,
    LiquidationsCore,
    LiquidationsPeripheral,
    LiquidityControls,
    web3
)
from brownie.network.gas.strategies import GasNowScalingStrategy
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

gas_strategy = GasNowScalingStrategy("fast", increment=1.2)

NAME_TO_CONTRACT = {
    "collateral_vault_core": CollateralVaultCore,
    "cryptopunks_vault_core": CryptoPunksVaultCore,
    "collateral_vault_peripheral": CollateralVaultPeripheral,
    "lending_pool_core": LendingPoolCore,
    "lending_pool": LendingPoolPeripheral,
    "liquidations_peripheral": LiquidationsPeripheral,
    "liquidations_core": LiquidationsCore,
    "liquidity_controls": LiquidityControls,
    "loans": Loans,
    "loans_core": LoansCore,
    "token": ERC20
}


def load_contracts(env: str) -> dict:
    config_file = f"{Path.cwd()}/configs/{env}/contracts.json"
    with open(config_file, "r") as f:
        contracts = json.load(f)["tokens"]["WETH"]

    return {key: NAME_TO_CONTRACT[key].at(contracts[key]["contract"]) for key in contracts}


def load_nft_contracts(env: str) -> dict:
    config_file = f"{Path.cwd()}/configs/{env}/nfts.json"
    with open(config_file, "r") as f:
        contracts = json.load(f)

    return {
        "cool_cats_instance": ERC721.at(contracts[0]["contract"]),
        "hashmasks_instance": ERC721.at(contracts[1]["contract"]),
        "kennel_instance": ERC721.at(contracts[2]["contract"]),
        "doodles_instance": ERC721.at(contracts[3]["contract"]),
        "wow_instance": ERC721.at(contracts[4]["contract"]),
        "mutant_instance": ERC721.at(contracts[5]["contract"]),
        "veefriends_instance": ERC721.at(contracts[6]["contract"]),
        "pudgypenguins_instance": ERC721.at(contracts[7]["contract"]),
        "bayc_instance": ERC721.at(contracts[8]["contract"]),
        "wpunks_instance": ERC721.at(contracts[9]["contract"]),
        "cryptopunks_instance": ERC721.at(contracts[10]["contract"])
    }


def prod():
    owner = accounts.load("prodacc")

    contracts = load_contracts("prod")
    nft_contracts = load_nft_contracts("prod")

    cool_cats_instance = nft_contracts["cool_cats_instance"]
    hashmasks_instance = nft_contracts["hashmasks_instance"]
    kennel_instance = nft_contracts["kennel_instance"]
    doodles_instance = nft_contracts["doodles_instance"]
    wow_instance = nft_contracts["wow_instance"]
    mutant_instance = nft_contracts["mutant_instance"]
    veefriends_instance = nft_contracts["veefriends_instance"]
    pudgypenguins_instance = nft_contracts["pudgypenguins_instance"]
    bayc_instance = nft_contracts["bayc_instance"]
    wpunks_instance = nft_contracts["wpunks_instance"]
    cryptopunks_instance = nft_contracts["cryptopunks_instance"]

    weth = contracts["token"]
    loans_core_weth = contracts["loans_core"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidations_peripheral = contracts["liquidations_peripheral"]
    collateral_vault_peripheral = contracts["collateral_vault_peripheral"]
    liquidity_controls = contracts["liquidity_controls"]

    loans_peripheral_weth = Loans.deploy(
        1000000,
        31 * 86400,
        web3.toWei(10000, "ether"),
        24 * 60 * 60,
        loans_core_weth,
        lending_pool_peripheral_weth,
        collateral_vault_peripheral,
        {"from": owner, "gas_price": web3.toWei(20, "gwei")}
    )

    lending_pool_peripheral_weth.setLoansPeripheralAddress(
        loans_peripheral_weth,
        {"from": owner, "gas_price": web3.toWei(20, "gwei")}
    )

    collateral_vault_peripheral.addLoansPeripheralAddress(
        weth,
        loans_peripheral_weth,
        {"from": owner, "gas_price": web3.toWei(20, "gwei")}
    )

    loans_core_weth.setLoansPeripheral(
        loans_peripheral_weth,
        {"from": owner, "gas_price": web3.toWei(20, "gwei")}
    )

    loans_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner, "gas_price": web3.toWei(20, "gwei")}
    )
    loans_peripheral_weth.setLiquidityControlsAddress(
        liquidity_controls,
        {"from": owner, "gas_price": web3.toWei(20, "gwei")}
    )

    loans_peripheral_weth.addCollateralToWhitelist(cool_cats_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(hashmasks_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(kennel_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(doodles_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(wow_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(mutant_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(veefriends_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(pudgypenguins_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(bayc_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(wpunks_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    loans_peripheral_weth.addCollateralToWhitelist(cryptopunks_instance, {"from": owner, "gas_price": web3.toWei(20, "gwei")})

    liquidity_controls.changeMaxCollectionBorrowableAmount(True, cryptopunks_instance, web3.toWei(750, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, wpunks_instance, web3.toWei(750, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, bayc_instance, web3.toWei(500, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, doodles_instance, web3.toWei(50, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, pudgypenguins_instance, web3.toWei(35, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, mutant_instance, web3.toWei(75, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, veefriends_instance, web3.toWei(35, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, kennel_instance, web3.toWei(35, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, wow_instance, web3.toWei(25, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, cool_cats_instance, web3.toWei(25, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, hashmasks_instance, web3.toWei(5, "ether"), {"from": owner, "gas_price": web3.toWei(20, "gwei")})

def main():
    prod()
    pass