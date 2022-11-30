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


def main():
    owner = accounts.load('goerliacc')

    ### TEST NFT CONTRACTS ###
    cool_cats_instance = ERC721.deploy({"from": owner})
    hashmasks_instance = ERC721.deploy({"from": owner})
    kennel_instance = ERC721.deploy({"from": owner})
    doodles_instance = ERC721.deploy({"from": owner})
    wow_instance = ERC721.deploy({"from": owner})
    mutant_instance = ERC721.deploy({"from": owner})
    veefriends_instance = ERC721.deploy({"from": owner})
    pudgypenguins_instance = ERC721.deploy({"from": owner})
    bayc_instance = ERC721.deploy({"from": owner})
    wpunks_instance = ERC721.deploy({"from": owner})

    ### TEST WETH CONTRACT ###
    weth = ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {'from': owner})

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

    cryptopunks_instance = ERC721.deploy({"from": owner})
    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})

    collateral_vault_peripheral = CollateralVaultPeripheral.deploy(
        collateral_vault_core,
        {"from": owner}
    )
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_core_weth = LoansCore.deploy({"from": owner})

    loans_peripheral_weth = Loans.deploy(
        1000000,
        31 * 86400,
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
        172800,
        1296000,
        1296000,
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

    loans_peripheral_weth.addCollateralToWhitelist(cool_cats_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(hashmasks_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(kennel_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(doodles_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(wow_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(mutant_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(veefriends_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(pudgypenguins_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(bayc_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(wpunks_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(cryptopunks_instance, {"from": owner})
