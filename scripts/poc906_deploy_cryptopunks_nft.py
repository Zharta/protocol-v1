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
from pathlib import Path


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
    cryptopunks_instance = ERC721.deploy({"from": owner})
    print(f"cryptopunks address={cryptopunks_instance.address}")

    weth = contracts["token"]
    collateral_vault_core = contracts["collateral_vault_core"]
    liquidations_core = contracts["liquidations_core"]
    loans_core_weth = contracts["loans_core"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidity_controls = contracts["liquidity_controls "]

    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})
    print(f"cryptopunks_vault_core address={cryptopunks_vault_core.address}")

    collateral_vault_peripheral = CollateralVaultPeripheral.deploy(
        collateral_vault_core,
        {"from": owner}
    )
    print(f"collateral_vault_peripheral address={collateral_vault_peripheral.address}")

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
    print(f"loans_peripheral_weth address={loans_peripheral_weth.address}")

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        172800,
        172800,
        172800,
        weth,
        {"from": owner}
    )
    print(f"liquidations_peripheral address={liquidations_peripheral.address}")

    lending_pool_peripheral_weth.setLoansPeripheralAddress(
        loans_peripheral_weth,
        {"from": owner}
    )
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    collateral_vault_peripheral.addVault(
        cryptopunks_instance,
        cryptopunks_vault_core,
        {"from": owner}
    )

    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
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
    cryptopunks_instance = ERC721.deploy({"from": owner})
    print(f"cryptopunks address={cryptopunks_instance.address}")

    weth = contracts["token"]
    collateral_vault_core = contracts["collateral_vault_core"]
    liquidations_core = contracts["liquidations_core"]
    loans_core_weth = contracts["loans_core"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidity_controls = contracts["liquidity_controls "]

    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})
    print(f"cryptopunks_vault_core address={cryptopunks_vault_core.address}")

    collateral_vault_peripheral = CollateralVaultPeripheral.deploy(
        collateral_vault_core,
        {"from": owner}
    )
    print(f"collateral_vault_peripheral address={collateral_vault_peripheral.address}")

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
    print(f"loans_peripheral_weth address={loans_peripheral_weth.address}")

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        172800,
        172800,
        172800,
        weth,
        {"from": owner}
    )
    print(f"liquidations_peripheral address={liquidations_peripheral.address}")

    lending_pool_peripheral_weth.setLoansPeripheralAddress(
        loans_peripheral_weth,
        {"from": owner}
    )
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    collateral_vault_peripheral.addVault(
        cryptopunks_instance,
        cryptopunks_vault_core,
        {"from": owner}
    )

    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
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
    collateral_vault_core = contracts["collateral_vault_core"]
    liquidations_core = contracts["liquidations_core"]
    loans_core_weth = contracts["loans_core"]
    lending_pool_peripheral_weth = contracts["lending_pool"]
    liquidity_controls = contracts["liquidity_controls "]

    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})
    print(f"cryptopunks_vault_core address={cryptopunks_vault_core.address}")

    collateral_vault_peripheral = CollateralVaultPeripheral.deploy(
        collateral_vault_core,
        {"from": owner}
    )
    print(f"collateral_vault_peripheral address={collateral_vault_peripheral.address}")

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
    print(f"loans_peripheral_weth address={loans_peripheral_weth.address}")

    liquidations_peripheral = LiquidationsPeripheral.deploy(
        liquidations_core,
        172800,
        172800,
        172800,
        weth,
        {"from": owner}
    )
    print(f"liquidations_peripheral address={liquidations_peripheral.address}")

    lending_pool_peripheral_weth.setLoansPeripheralAddress(
        loans_peripheral_weth,
        {"from": owner}
    )
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(
        liquidations_peripheral,
        {"from": owner}
    )
    collateral_vault_peripheral.addVault(
        cryptopunks_instance,
        cryptopunks_vault_core,
        {"from": owner}
    )

    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(
        collateral_vault_peripheral,
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


def main():
    # prod()
    pass
