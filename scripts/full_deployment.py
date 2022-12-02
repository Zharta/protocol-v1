import json

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
        "wpunks_instance": ERC721.at(contracts[9]["contract"])
    }


def dev():
    owner = accounts[0]

    contracts = load_contracts("dev")
    nft_contracts = load_nft_contracts("dev")

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

    ### TEST WETH CONTRACT ###
    weth = contracts["weth"]

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
        2 * 86400,
        2 * 86400,
        2 * 86400,
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


def int():
    owner = accounts.load("goerliacc")

    contracts = load_contracts("int")
    nft_contracts = load_nft_contracts("int")

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

    ### TEST WETH CONTRACT ###
    weth = contracts["weth"]

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
        2 * 86400,
        2 * 86400,
        2 * 86400,
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

    weth = contracts["weth"]

    ### PROTOCOL CONTRACTS ###
    lending_pool_core_weth = LendingPoolCore.deploy(weth, {"from": owner})

    lending_pool_peripheral_weth = LendingPoolPeripheral.deploy(
        lending_pool_core_weth,
        weth,
        "0x07d96cC26566BFCA358C61fBe7be3Ca771Da7EA6",
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
        2 * 86400,
        2 * 86400,
        2 * 86400,
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
    loans_peripheral_weth.addCollateralToWhitelist(bayc_instance, {"from": owner})
    loans_peripheral_weth.addCollateralToWhitelist(wpunks_instance, {"from": owner})

    liquidity_controls.changeMaxCollectionBorrowableAmount(True, wpunks_instance, web3.toWei(750, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, bayc_instance, web3.toWei(500, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, doodles_instance, web3.toWei(50, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, pudgypenguins_instance, web3.toWei(35, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, mutant_instance, web3.toWei(75, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, veefriends_instance, web3.toWei(35, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, kennel_instance, web3.toWei(35, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, wow_instance, web3.toWei(25, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, cool_cats_instance, web3.toWei(25, "ether"))
    liquidity_controls.changeMaxCollectionBorrowableAmount(True, hashmasks_instance, web3.toWei(5, "ether"))


def main():
    # prod()
    pass
