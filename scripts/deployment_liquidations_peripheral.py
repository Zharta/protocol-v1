import json

from brownie import (
    accounts,
    CollateralVaultCore,
    CollateralVaultPeripheral,
    LendingPoolCore,
    LendingPoolPeripheral,
    LiquidationsPeripheral,
    LiquidationsCore,
    LiquidityControls,
    LoansCore,
    Loans,
    ERC20
)
from pathlib import Path


NAME_TO_CONTRACT = {
    "collateral_vault_core": CollateralVaultCore,
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


def dev():
    owner = accounts[0]

    contracts = load_contracts("dev")

    weth = contracts["weth"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidations_core = contracts["liquidations_core"]
    collateral_vault_peripheral = contracts["collateral_vault_peripheral"]
    loans_peripheral_weth = contracts["loans"]
    loans_core_weth = contracts["loans_core"]

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        2 * 86400,
        2 * 86400,
        2 * 86400,
        weth,
        {"from": owner},
    )

    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    collateral_vault_peripheral.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    loans_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    liquidations_core.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    liquidations_peripheral.addLoansCoreAddress(
        weth,
        loans_core_weth,
        {"from": owner}
    )
    liquidations_peripheral.addLendingPoolPeripheralAddress(
        weth,
        lending_pool_peripheral_weth,
        {"from": owner}
    )
    liquidations_peripheral.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
        {"from": owner}
    )


def int():
    owner = accounts.load("goerliacc")

    contracts = load_contracts("int")

    weth = contracts["weth"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidations_core = contracts["liquidations_core"]
    collateral_vault_peripheral = contracts["collateral_vault_peripheral"]
    loans_peripheral_weth = contracts["loans"]
    loans_core_weth = contracts["loans_core"]

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        2 * 86400,
        2 * 86400,
        2 * 86400,
        weth,
        {"from": owner},
    )

    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    collateral_vault_peripheral.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    loans_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    liquidations_core.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    liquidations_peripheral.addLoansCoreAddress(
        weth,
        loans_core_weth,
        {"from": owner}
    )
    liquidations_peripheral.addLendingPoolPeripheralAddress(
        weth,
        lending_pool_peripheral_weth,
        {"from": owner}
    )
    liquidations_peripheral.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
        {"from": owner}
    )


def prod():
    owner = accounts.load("prodacc")

    contracts = load_contracts("int")

    weth = contracts["weth"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidations_core = contracts["liquidations_core"]
    collateral_vault_peripheral = contracts["collateral_vault_peripheral"]
    loans_peripheral_weth = contracts["loans"]
    loans_core_weth = contracts["loans_core"]

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        2 * 86400,
        2 * 86400,
        2 * 86400,
        weth,
        {"from": owner},
    )

    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    collateral_vault_peripheral.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    loans_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    liquidations_core.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )

    liquidations_peripheral.addLoansCoreAddress(
        weth,
        loans_core_weth,
        {"from": owner}
    )
    liquidations_peripheral.addLendingPoolPeripheralAddress(
        weth,
        lending_pool_peripheral_weth,
        {"from": owner}
    )
    liquidations_peripheral.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
        {"from": owner}
    )
    liquidations_peripheral.setNFTXVaultFactoryAddress(
        "0xBE86f647b167567525cCAAfcd6f881F1Ee558216",
        {"from": owner}
    )
    liquidations_peripheral.setNFTXMarketplaceZapAddress(
        "0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d",
        {"from": owner}
    )
    liquidations_peripheral.setSushiRouterAddress(
        "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        {"from": owner}
    )


def main():
    # dev()
    print(load_contracts("int"))
    pass
