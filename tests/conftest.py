import ape
import boa
from web3 import Web3, eth
from datetime import datetime as dt
from .conftest_base import get_last_event

from . import conftest_base
import pytest


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

LOAN_AMOUNT = Web3.to_wei(0.1, "ether")
INTEREST_ACCRUAL_PERIOD = 24 * 60 * 60

PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000

GRACE_PERIOD_DURATION = 50 # 2 days
LENDER_PERIOD_DURATION = 50 # 15 days
AUCTION_DURATION = 50 # 15 days

MAX_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_LOANS_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


@pytest.fixture(scope="session")
def accounts():
    _accounts = [boa.env.generate_address() for _ in range(10)]
    for account in _accounts:
        boa.env.set_balance(account, 10**21)
    return _accounts


@pytest.fixture(scope="session")
def owner_account():
    return eth.Account.create()


@pytest.fixture(scope="session")
def not_contract_owner_account():
    return eth.Account.create()


@pytest.fixture(scope="session", autouse=True)
def contract_owner(accounts, owner_account):
    # boa.env.eoa = accounts[0]  # avoid all the pranks in test setups
    # return accounts[0]
    boa.env.eoa = owner_account.address
    boa.env.set_balance(owner_account.address, 10**21)
    return owner_account.address

@pytest.fixture(scope="session")
def investor(accounts):
    return accounts[1]


@pytest.fixture(scope="session")
def borrower(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def erc20_contract(contract_owner, accounts):
    erc20 = boa.load_partial("tests/stubs/ERC20.vy").at("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    for account in accounts:
        erc20.deposit(sender=account, value=10**19)
    return erc20


@pytest.fixture(scope="session")
def erc721_contract(project, contract_owner):
    return boa.load("contracts/auxiliary/token/ERC721.vy")


@pytest.fixture(scope="session")
def collateral_vault_core_contract(contract_owner):
    with boa.env.prank(contract_owner):
        return boa.load("contracts/CollateralVaultCore.vy")


@pytest.fixture(scope="session")
def cryptopunks_market_contract(contract_owner):
    try:
        return boa.load_partial("tests/stubs/CryptoPunksMarketStub.vy").at("0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB")
    except Exception:
        return None


@pytest.fixture(scope="session")
def wpunks_contract(contract_owner):
    try:
        return boa.load_partial("tests/stubs/WrappedPunkStub.vy").at("0xb7F7F6C52F2e2fdb1963Eab30438024864c313F6")
    except Exception:
        return None


@pytest.fixture(scope="session")
def hashmasks_contract(contract_owner):
    return boa.load_partial("contracts/auxiliary/token/ERC721.vy").at("0xC2C747E0F7004F9E8817Db2ca4997657a7746928")


@pytest.fixture(scope="session")
def cryptopunks_vault_core_contract(cryptopunks_market_contract, contract_owner):
    return boa.load("contracts/CryptoPunksVaultCore.vy", cryptopunks_market_contract.address)


@pytest.fixture(scope="session")
def collateral_vault_peripheral_contract(collateral_vault_core_contract, contract_owner):
    return boa.load("contracts/CollateralVaultPeripheral.vy", collateral_vault_core_contract)


@pytest.fixture(scope="session")
def loans_core_contract(contract_owner):
    return boa.load("contracts/LoansCore.vy")


@pytest.fixture(scope="session")
def lending_pool_core_contract(erc20_contract, contract_owner):
    return boa.load("contracts/LendingPoolCore.vy", erc20_contract)


@pytest.fixture(scope="session")
def lending_pool_lock_contract(erc20_contract, contract_owner):
    return boa.load("contracts/LendingPoolLock.vy", erc20_contract)


@pytest.fixture(scope="session")
def lending_pool_peripheral_contract(lending_pool_core_contract, lending_pool_lock_contract, erc20_contract, contract_owner, protocol_wallet):
    return boa.load(
        "contracts/LendingPoolPeripheral.vy",
        lending_pool_core_contract,
        lending_pool_lock_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
    )


@pytest.fixture(scope="session")
def lending_pool_peripheral_contract_aux(lending_pool_core_contract, lending_pool_lock_contract, erc20_contract, contract_owner, protocol_wallet):
    return boa.load(
        "contracts/LendingPoolPeripheral.vy",
        lending_pool_core_contract,
        lending_pool_lock_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
    )


@pytest.fixture(scope="session")
def loans_peripheral_contract(loans_core_contract, lending_pool_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    return boa.load(
        "contracts/Loans.vy",
        INTEREST_ACCRUAL_PERIOD,
        loans_core_contract,
        lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
    )


@pytest.fixture(scope="session")
def loans_peripheral_contract_aux(lending_pool_peripheral_contract, contract_owner, accounts):
    return boa.load(
        "contracts/Loans.vy",
        INTEREST_ACCRUAL_PERIOD,
        accounts[4],
        lending_pool_peripheral_contract,
        accounts[5],
    )


@pytest.fixture(scope="session")
def liquidations_core_contract(contract_owner):
    return boa.load("contracts/LiquidationsCore.vy")


@pytest.fixture(scope="session")
def liquidations_peripheral_contract(liquidations_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract = boa.load(
        "contracts/LiquidationsPeripheral.vy",
        liquidations_core_contract,
        GRACE_PERIOD_DURATION,
        LENDER_PERIOD_DURATION,
        AUCTION_DURATION,
        erc20_contract,
    )
    liquidations_peripheral_contract.setNFTXVaultFactoryAddress("0xBE86f647b167567525cCAAfcd6f881F1Ee558216")
    liquidations_peripheral_contract.setNFTXMarketplaceZapAddress("0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d")
    liquidations_peripheral_contract.setSushiRouterAddress("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    return liquidations_peripheral_contract


@pytest.fixture(scope="session")
def liquidity_controls_contract(contract_owner):
    return boa.load(
        "contracts/LiquidityControls.vy",
        False,
        MAX_POOL_SHARE,
        False,
        LOCK_PERIOD_DURATION,
        False,
        MAX_LOANS_POOL_SHARE,
        False,
    )


@pytest.fixture(scope="session")
def test_collaterals(erc721_contract):
    result = []
    for k in range(5):
        result.append((erc721_contract.address, k, LOAN_AMOUNT // 5))
    return result


@pytest.fixture(scope="session")
def cryptopunk_collaterals(cryptopunks_market_contract, borrower):
    result = []
    if cryptopunks_market_contract is None:
        return result
    for k in range(5):
        owner = cryptopunks_market_contract.punkIndexToAddress(k)
        with boa.env.prank(owner):
            cryptopunks_market_contract.transferPunk(borrower, k, sender=owner)
        result.append((cryptopunks_market_contract, k, LOAN_AMOUNT // 5))
    return result


@pytest.fixture(scope="module")
def contracts_config(
    collateral_vault_core_contract,
    collateral_vault_peripheral_contract,
    contract_owner,
    cryptopunks_market_contract,
    cryptopunks_vault_core_contract,
    erc20_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    lending_pool_peripheral_contract,
    liquidations_core_contract,
    liquidations_peripheral_contract,
    liquidity_controls_contract,
    loans_core_contract,
    loans_peripheral_contract,
    wpunks_contract,
):
    with boa.env.anchor():
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
        collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
        cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
        lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
        lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
        lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
        lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, sender=contract_owner)
        lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, sender=contract_owner)
        liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, sender=contract_owner)
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, sender=contract_owner)
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
        loans_core_contract.setLoansPeripheral(loans_peripheral_contract, sender=contract_owner)
        loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
        loans_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, sender=contract_owner)
        if cryptopunks_market_contract is not None:
            collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract, sender=contract_owner)
            liquidations_peripheral_contract.setCryptoPunksAddress(cryptopunks_market_contract, sender=contract_owner)
        if wpunks_contract is not None:
            liquidations_peripheral_contract.setWrappedPunksAddress(wpunks_contract, sender=contract_owner)
        yield

