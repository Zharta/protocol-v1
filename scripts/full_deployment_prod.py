from brownie import (
    accounts,
    ERC721,
    ERC20,
    LendingPoolCore,
    LendingPoolPeripheral,
    CollateralVaultCore,
    CollateralVaultPeripheral,
    LoansCore,
    Loans,
    LiquidationsCore,
    LiquidationsPeripheral,
    LiquidityControls,
    web3
)


def main():
    owner = accounts.load('prodacc')

    ### TEST NFT CONTRACTS ###
    cool_cats_instance = ERC721.at("0x1A92f7381B9F03921564a437210bB9396471050C")
    hashmasks_instance = ERC721.at("0xC2C747E0F7004F9E8817Db2ca4997657a7746928")
    kennel_instance = ERC721.at("0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623")
    doodles_instance = ERC721.at("0x8a90CAb2b38dba80c64b7734e58Ee1dB38B8992e")
    wow_instance = ERC721.at("0xe785E82358879F061BC3dcAC6f0444462D4b5330")
    mutant_instance = ERC721.at("0x60E4d786628Fea6478F785A6d7e704777c86a7c6")
    veefriends_instance = ERC721.at("0xa3AEe8BcE55BEeA1951EF834b99f3Ac60d1ABeeB")
    pudgypenguins_instance = ERC721.at("0xBd3531dA5CF5857e7CfAA92426877b022e612cf8")

    ### TEST WETH CONTRACT ###
    weth = ERC20.at("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    ### PROTOCOL CONTRACTS ###
    lending_pool_core_weth = LendingPoolCore.deploy(weth, {"from": owner})

    lending_pool_peripheral_weth = LendingPoolPeripheral.deploy(
        lending_pool_core_weth,
        weth,
        owner,
        2500,
        7000,
        False,
        {"from": owner}
    )
    
    collateral_vault_core = CollateralVaultCore.deploy({"from": owner})
    
    collateral_vault_peripheral = CollateralVaultPeripheral.deploy(
        collateral_vault_core,
        {"from": owner}
    )
    
    loans_core_weth = LoansCore.deploy({"from": owner})
    
    loans_peripheral_weth = Loans.deploy(
        1000000,
        2678400,
        web3.toWei(10000, "ether"),
        24 * 60 * 60,
        loans_core_weth,
        lending_pool_peripheral_weth,
        collateral_vault_peripheral,
        {"from": owner}
    )

    liquidations_core = LiquidationsCore.deploy({"from": owner})

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        180 * 86400,
        180 * 86400,
        180 * 86400,
        weth,
        {"from": owner},
    )

    liquidity_controls = LiquidityControls.deploy(
        False,
        1500,
        False,
        7 * 24 * 60 * 60,
        False,
        1500,
        False,
        5000,
        {"from": owner}
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
    
    collateral_vault_core.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
        {"from": owner}
    )
    
    collateral_vault_peripheral.addLoansPeripheralAddress(
        weth,
        loans_peripheral_weth,
        {"from": owner}
    )
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    
    loans_core_weth.setLoansPeripheral(
        loans_peripheral_weth,
        {"from": owner}
    )
    
    loans_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    loans_peripheral_weth.setLiquidityControlsAddress(
        liquidity_controls,
        {"from": owner}
    )
    
    liquidations_core.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    liquidations_core.addLoansCoreAddress(
        weth,
        loans_core_weth,
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

    loans_peripheral_weth.addCollateralToWhitelist(cool_cats_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(hashmasks_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(kennel_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(doodles_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(wow_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(mutant_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(veefriends_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(pudgypenguins_instance, {"from": owner})

