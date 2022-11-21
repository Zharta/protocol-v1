from brownie import (
    accounts,
    ERC20,
    LendingPoolPeripheral,
    CollateralVaultPeripheral,
    LoansCore,
    Loans,
    LiquidationsCore,
    LiquidationsPeripheral
)

def main():
    owner = accounts.load('goerliacc')

    weth = ERC20.at("0x96D1000886E9F504184068DE3cd1270f0e00b286")
    lending_pool_peripheral_weth = LendingPoolPeripheral.at("0x5A4b9aeFcEd0BBAf2a5cf81852b2Acb666ADEF45")
    liquidations_core = LiquidationsCore.at("0xC576a9Db2f307dA4C6C332913E860C839280C561")
    collateral_vault_peripheral = CollateralVaultPeripheral.at("0xEedfDfC9F79391Fd09FFAE0720B77c4E2149e414")
    loans_peripheral_weth = Loans.at("0xD4986462b26e4a63D1c380f9C43776fC4C9e7f41")
    loans_core_weth = LoansCore.at("0x9917771853d4aB45e2132E4942E570d4A1d84cCb")

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
