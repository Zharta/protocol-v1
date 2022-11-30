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


def dev():
    owner = accounts[0]

    cool_cats_instance = ERC721.at('0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87')
    hashmasks_instance = ERC721.at('0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6')
    kennel_instance = ERC721.at('0xE7eD6747FaC5360f88a2EFC03E00d25789F69291')
    doodles_instance = ERC721.at('0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85')
    wow_instance = ERC721.at('0xe0aA552A10d7EC8760Fc6c246D391E698a82dDf9')
    mutant_instance = ERC721.at('0X6b4BDe1086912A6Cb24ce3dB43b3466e6c72AFd3')
    veefriends_instance = ERC721.at('0x9E4c14403d7d9A8A782044E86a93CAE09D7B2ac9')
    pudgypenguins_instance = ERC721.at('0xcCB53c9429d32594F404d01fbe9E65ED1DCda8D9')
    bayc_instance = ERC721.at('0x3981B4737bc9796A1Bf1b23bBB47Ec4104862f4f')
    wpunks_instance = ERC721.at('0x168b6B69003Fa56ba2E243ea892f5cf2D09d049a')
    cryptopunks_instance = ERC721.deploy({"from": owner})
    print(f"cryptopunks address={cryptopunks_instance.address}")

    collateral_vault_core = CollateralVaultCore.at('0x2c15A315610Bfa5248E4CbCbd693320e9D8E03Cc')
    liquidations_core = LiquidationsCore.at('0x26f15335BB1C6a4C0B660eDd694a0555A9F1cce3')
    loans_core_weth = LoansCore.at('0xe65A7a341978d59d40d30FC23F5014FACB4f575A')
    lending_pool_peripheral_weth = LendingPoolPeripheral.at('0x7a3d735ee6873f17Dbdcab1d51B604928dc10d92')
    liquidity_controls = LiquidityControls.at('0xed00238F9A0F7b4d93842033cdF56cCB32C781c2')
    weth = ERC20.at('0x420b1099B9eF5baba6D92029594eF45E19A04A4A')

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
        1296000,
        1296000,
        weth,
        {"from": owner}
    )
    print(f"liquidations_peripheral address={liquidations_peripheral.address}")

    lending_pool_peripheral_weth.setLoansPeripheralAddress(loans_peripheral_weth, {"from": owner})
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})

    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})
    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})

    collateral_vault_peripheral.addLoansPeripheralAddress(weth, loans_peripheral_weth, {"from": owner})
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_core_weth.setLoansPeripheral(loans_peripheral_weth, {"from": owner})
    loans_peripheral_weth.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    loans_peripheral_weth.setLiquidityControlsAddress(liquidity_controls, {"from": owner})

    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    liquidations_peripheral.addLoansCoreAddress(weth, loans_core_weth, {"from": owner})
    liquidations_peripheral.addLendingPoolPeripheralAddress(weth, lending_pool_peripheral_weth, {"from": owner})
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})

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
    owner = accounts.load('goerliacc')

    cool_cats_instance = ERC721.at('0x69B5cfEfDd30467Ea985EBac1756d81EA871798c')
    hashmasks_instance = ERC721.at('0xBE14483462B90b2e11f624f5A91aFc2F3562d871')
    kennel_instance = ERC721.at('0xA8Ab83613fF003B841E6831b97AA462b4B6b520A')
    doodles_instance = ERC721.at('0x2F886AAD50d76258C1E77AC92a57Df1d5DB48853')
    wow_instance = ERC721.at('0xB16A9612b91259ABA40862233e25f9685Ea0d738')
    mutant_instance = ERC721.at('0x5c435249e08D987a77fdA86376e796C37C552136')
    veefriends_instance = ERC721.at('0x69f18335Ab0c6E60C7cE02e501BBCb0C25025eDc')
    pudgypenguins_instance = ERC721.at('0x311F9f063a3e8de0fFe81beAca53EEC310432faE')
    bayc_instance = ERC721.at('0xFcbB8A298CA9EF27C16890bab01C0613723e57e8')
    wpunks_instance = ERC721.at('0x94aF590c1001dA77773335B3629382b23Dd7aB22')
    cryptopunks_instance = ERC721.deploy({"from": owner})
    print(f"cryptopunks address={cryptopunks_instance.address}")

    collateral_vault_core = CollateralVaultCore.at('0x170a934DB411912D2D557F28B3866b994e246b83')
    liquidations_core = LiquidationsCore.at('0xC576a9Db2f307dA4C6C332913E860C839280C561')
    loans_core_weth = LoansCore.at('0x9917771853d4aB45e2132E4942E570d4A1d84cCb')
    lending_pool_peripheral_weth = LendingPoolPeripheral.at('0x5A4b9aeFcEd0BBAf2a5cf81852b2Acb666ADEF45')
    liquidity_controls = LiquidityControls.at('0x4c59ab2e0F8B875b2Af9b7Cebb2822DBDB791bDf')
    weth = ERC20.at('0x96D1000886E9F504184068DE3cd1270f0e00b286')

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
        1296000,
        1296000,
        weth,
        {"from": owner}
    )
    print(f"liquidations_peripheral address={liquidations_peripheral.address}")

    lending_pool_peripheral_weth.setLoansPeripheralAddress(loans_peripheral_weth, {"from": owner})
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})

    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})
    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})

    collateral_vault_peripheral.addLoansPeripheralAddress(weth, loans_peripheral_weth, {"from": owner})
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_core_weth.setLoansPeripheral(loans_peripheral_weth, {"from": owner})
    loans_peripheral_weth.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    loans_peripheral_weth.setLiquidityControlsAddress(liquidity_controls, {"from": owner})

    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    liquidations_peripheral.addLoansCoreAddress(weth, loans_core_weth, {"from": owner})
    liquidations_peripheral.addLendingPoolPeripheralAddress(weth, lending_pool_peripheral_weth, {"from": owner})
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})

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
    owner = accounts.load('prodacc')

    cool_cats_instance = ERC721.at('0x1A92f7381B9F03921564a437210bB9396471050C')
    hashmasks_instance = ERC721.at('0xC2C747E0F7004F9E8817Db2ca4997657a7746928')
    kennel_instance = ERC721.at('0xba30E5F9Bb24caa003E9f2f0497Ad287FDF95623')
    doodles_instance = ERC721.at('0x8a90CAb2b38dba80c64b7734e58Ee1dB38B8992e')
    wow_instance = ERC721.at('0xe785E82358879F061BC3dcAC6f0444462D4b5330')
    mutant_instance = ERC721.at('0x60E4d786628Fea6478F785A6d7e704777c86a7c6')
    veefriends_instance = ERC721.at('0xa3AEe8BcE55BEeA1951EF834b99f3Ac60d1ABeeB')
    pudgypenguins_instance = ERC721.at('0xBd3531dA5CF5857e7CfAA92426877b022e612cf8')
    bayc_instance = ERC721.at('0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D')
    wpunks_instance = ERC721.at('0xb7F7F6C52F2e2fdb1963Eab30438024864c313F6')
    cryptopunks_instance = ERC721.at('0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB')

    collateral_vault_core = CollateralVaultCore.at('0xA79da8c90Aa480B3716C23145154CA6eF5Fc29C1')
    liquidations_core = LiquidationsCore.at('0x53DE37d93A374d8B3719befA0343f26365E30cE9')
    loans_core_weth = LoansCore.at('0x454d32EE8B6A98fC21cf93D9ef02F3cCbef92D79')
    lending_pool_peripheral_weth = LendingPoolPeripheral.at('0x3bd1485BC0b2f2d2864Cc0a92ec9006803F40f85')
    liquidity_controls = LiquidityControls.at('0x424C836aBCf82bEE373C378fA6Efc0690EFEec93')
    weth = ERC20.at('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')

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
        1296000,
        1296000,
        weth,
        {"from": owner}
    )
    print(f"liquidations_peripheral address={liquidations_peripheral.address}")

    lending_pool_peripheral_weth.setLoansPeripheralAddress(loans_peripheral_weth, {"from": owner})
    lending_pool_peripheral_weth.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})

    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})
    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})

    collateral_vault_peripheral.addLoansPeripheralAddress(weth, loans_peripheral_weth, {"from": owner})
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    collateral_vault_peripheral.addVault(cryptopunks_instance, cryptopunks_vault_core, {"from": owner})

    loans_core_weth.setLoansPeripheral(loans_peripheral_weth, {"from": owner})
    loans_peripheral_weth.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    loans_peripheral_weth.setLiquidityControlsAddress(liquidity_controls, {"from": owner})

    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, {"from": owner})
    liquidations_peripheral.addLoansCoreAddress(weth, loans_core_weth, {"from": owner})
    liquidations_peripheral.addLendingPoolPeripheralAddress(weth, lending_pool_peripheral_weth, {"from": owner})
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, {"from": owner})

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
    # dev()
    pass
