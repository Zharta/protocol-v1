from brownie import(
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
# TODO add to full_deployment_*

def dev():
    owner = accounts[0]
    cryptopunks_instance = ERC721.deploy({"from": owner})
    print(f"cryptopunks address={cryptopunks_instance.address}")

    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})
    print(f"cryptopunks_vault_core address={cryptopunks_vault_core.address}")

    collateral_vault_peripheral = CollateralVaultPeripheral.at('0xe692Cf21B12e0B2717C4bF647F9768Fa58861c8b')
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_peripheral_weth = Loans.at('0x3D9e3ABd15E695fc0E49386D9F8719537714347F')
    loans_peripheral_weth.addCollateralToWhitelist(cryptopunks_instance, {"from": owner})


def int():
    owner = accounts.load('goerliacc')
    cryptopunks_instance = ERC721.deploy({"from": owner})
    print(f"cryptopunks address={cryptopunks_instance.address}")

    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})
    print(f"cryptopunks_vault_core address={cryptopunks_vault_core.address}")

    collateral_vault_peripheral = CollateralVaultPeripheral.at('0xEedfDfC9F79391Fd09FFAE0720B77c4E2149e414')
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_peripheral_weth = Loans.at('0xD4986462b26e4a63D1c380f9C43776fC4C9e7f41')
    loans_peripheral_weth.addCollateralToWhitelist(cryptopunks_instance, {"from": owner})


def prod():
    owner = accounts.load('prodacc')
    cryptopunks_instance = ERC721.at('0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB')

    cryptopunks_vault_core = CryptoPunksVaultCore.deploy(cryptopunks_instance, {"from": owner})
    print(f"cryptopunks_vault_core address={cryptopunks_vault_core.address}")

    collateral_vault_peripheral = CollateralVaultPeripheral.at('0x4EB10b069d11C73aAE86CEdf22C03D881A5F8453')
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_peripheral_weth = Loans.at('0x454d32EE8B6A98fC21cf93D9ef02F3cCbef92D79')
    loans_peripheral_weth.addCollateralToWhitelist(cryptopunks_instance, {"from": owner})


def main():
    # dev()
    pass
