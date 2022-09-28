from brownie import (
    accounts,
    ERC20,
    LendingPoolCore,
    LendingPoolPeripheral,
    CollateralVaultPeripheral,
    LoansCore,
    Loans,
    LiquidationsCore,
    LiquidationsPeripheral,
    LiquidityControls,
)


def main():
    owner = accounts.load('prodacc')

    ### TEST WETH CONTRACT ###
    weth = ERC20.at("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    ### PROTOCOL CONTRACTS ###
    lending_pool_core_weth = LendingPoolCore.at("0x409F6CaAa48e30041e201A2a839C01185d05D3ca")
    collateral_vault_peripheral = CollateralVaultPeripheral.at("0x44D2f0F514BF0ea91d9B19dcC7b1D8247A349FE1")
    loans_core_weth = LoansCore.at("0x7767A2b2F490622c7625eb236ACa221859418B20")
    loans_peripheral_weth = Loans.at("0x6781884f919B3533B4de87715e0E4564E62912fE")
    liquidations_core = LiquidationsCore.at("0x3E02654FbD6580f0D3F2E7999E53b0428bC88373")
    liquidity_controls = LiquidityControls.at("0x02325e1773BE685384f1ad0f619CFa6c901E419E")

    lending_pool_peripheral_weth = LendingPoolPeripheral.deploy(
        lending_pool_core_weth,
        weth,
        owner,
        2500,
        7000,
        False,
        {"from": owner}
    )

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        172800,
        1296000,
        1296000,
        weth,
        {"from": owner},
    )

    ### PROTOCOL CONFIGURATIONS ###
    lending_pool_core_weth.setLendingPoolPeripheralAddress(
        lending_pool_peripheral_weth,
        {"from": owner}
    )
    
    lending_pool_peripheral_weth.setLoansPeripheralAddress(
        loans_peripheral_weth,
        {"from": owner}
    )
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    lending_pool_peripheral_weth.setLiquidityControlsAddress(
        liquidity_controls,
        {"from": owner}
    )
    
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    
    loans_peripheral_weth.setLendingPoolPeripheralAddress(
        lending_pool_peripheral_weth,
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
