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
    owner = accounts.load('prodacc')

    weth = ERC20.at("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    lending_pool_peripheral_weth = LendingPoolPeripheral.at("0x0b2D6a2106be311D6d9c9EC8c0971f554691cC45")
    liquidations_core = LiquidationsCore.at("0x3E02654FbD6580f0D3F2E7999E53b0428bC88373")
    collateral_vault_peripheral = CollateralVaultPeripheral.at("0x44D2f0F514BF0ea91d9B19dcC7b1D8247A349FE1")
    loans_peripheral_weth = Loans.at("0x6781884f919B3533B4de87715e0E4564E62912fE")
    loans_core_weth = LoansCore.at("0x7767A2b2F490622c7625eb236ACa221859418B20")

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
