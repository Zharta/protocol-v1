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
    owner = accounts[0]

    ### TEST WETH CONTRACT ###
    weth = ERC20.at("0x420b1099B9eF5baba6D92029594eF45E19A04A4A")

    ### PROTOCOL CONTRACTS ###
    lending_pool_core_weth = LendingPoolCore.at("0xb6286fAFd0451320ad6A8143089b216C2152c025")

    lending_pool_peripheral_weth = LendingPoolPeripheral.deploy(
        lending_pool_core_weth,
        weth,
        owner,
        2500,
        7000,
        False,
        {"from": owner}
    )
    
    collateral_vault_peripheral = CollateralVaultPeripheral.at("0xe692Cf21B12e0B2717C4bF647F9768Fa58861c8b")
    loans_core_weth = LoansCore.at("0xe65A7a341978d59d40d30FC23F5014FACB4f575A")
    loans_peripheral_weth = Loans.at("0x30375B532345B01cB8c2AD12541b09E9Aa53A93d")
    liquidations_core = LiquidationsCore.at("0x26f15335BB1C6a4C0B660eDd694a0555A9F1cce3")

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        172800,
        1296000,
        1296000,
        weth,
        {"from": owner},
    )

    liquidity_controls = LiquidityControls.at("0xed00238F9A0F7b4d93842033cdF56cCB32C781c2")

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
