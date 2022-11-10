
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

def dev():
    owner = accounts[0]
    bayc_instance = ERC721.deploy({"from": owner})
    loans_peripheral_weth = Loans.at('0x3D9e3ABd15E695fc0E49386D9F8719537714347F')
    loans_peripheral_weth.addCollateralToWhitelist(bayc_instance, {"from": owner})

def int():
    owner = accounts.load('goerliacc')
    bayc_instance = ERC721.deploy({"from": owner})
    print(f"nft address={bayc_instance.address}")
    loans_peripheral_weth = Loans.at('0xD4986462b26e4a63D1c380f9C43776fC4C9e7f41')
    loans_peripheral_weth.addCollateralToWhitelist(bayc_instance, {"from": owner})

def prod():
    owner = accounts.load('prodacc')
    bayc_instance = ERC721.at('0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d')
    loans_peripheral_weth = Loans.at('0x454d32EE8B6A98fC21cf93D9ef02F3cCbef92D79')
    loans_peripheral_weth.addCollateralToWhitelist(bayc_instance, {"from": owner})

def main():
    # int()
    pass

