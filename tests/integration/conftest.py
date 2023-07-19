import boa
from web3 import Web3
from eth_account import Account
from ..conftest_base import get_last_event, ZERO_ADDRESS
from datetime import datetime as dt
from boa.environment import Env

import pytest
import os

LOAN_AMOUNT = Web3.to_wei(0.1, "ether")

LOAN_INTEREST = 250  # 2.5% in parts per 10000
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
def erc20_contract_def():
    return boa.load_partial("tests/stubs/ERC20.vy")


@pytest.fixture(scope="session")
def erc721_contract_def():
    return boa.load_partial("contracts/auxiliary/token/ERC721.vy")


@pytest.fixture(scope="session")
def cryptopunks_market_contract_def():
    return boa.load_partial("tests/stubs/CryptoPunksMarketStub.vy")


@pytest.fixture(scope="session")
def wpunks_contract_def():
    return boa.load_partial("tests/stubs/WrappedPunkStub.vy")


@pytest.fixture(scope="session")
def delegation_registry_contract_def():
    return boa.load_partial("contracts/auxiliary/delegate/DelegationRegistryMock.vy")


@pytest.fixture(scope="session")
def genesis_contract_def():
    return boa.load_partial("contracts/GenesisPass.vy")


@pytest.fixture(scope="session")
def collateral_vault_core_contract_def():
    return boa.load_partial("contracts/CollateralVaultCoreV2.vy")


@pytest.fixture(scope="session")
def cryptopunks_vault_core_contract_def():
    return boa.load_partial("contracts/CryptoPunksVaultCore.vy")


@pytest.fixture(scope="session")
def collateral_vault_peripheral_contract_def():
    return boa.load_partial("contracts/CollateralVaultPeripheral.vy")


@pytest.fixture(scope="session")
def collateral_vault_otc_contract_def():
    return boa.load_partial("contracts/CollateralVaultOTC.vy")


@pytest.fixture(scope="session")
def lending_pool_core_contract_def():
    return boa.load_partial("contracts/LendingPoolCore.vy")


@pytest.fixture(scope="session")
def lending_pool_lock_contract_def():
    return boa.load_partial("contracts/LendingPoolLock.vy")


@pytest.fixture(scope="session")
def lending_pool_peripheral_contract_def():
    return boa.load_partial("contracts/LendingPoolPeripheral.vy")


@pytest.fixture(scope="session")
def lending_pool_otc_contract_def():
    return boa.load_partial("contracts/LendingPoolOTC.vy")


@pytest.fixture(scope="session")
def loans_core_contract_def():
    return boa.load_partial("contracts/LoansCore.vy")


@pytest.fixture(scope="session")
def loans_peripheral_contract_def():
    return boa.load_partial("contracts/Loans.vy")


@pytest.fixture(scope="session")
def loans_otc_contract_def():
    return boa.load_partial("contracts/LoansOTC.vy")


@pytest.fixture(scope="session")
def liquidations_core_contract_def():
    return boa.load_partial("contracts/LiquidationsCore.vy")


@pytest.fixture(scope="session")
def liquidations_peripheral_contract_def():
    return boa.load_partial("contracts/LiquidationsPeripheral.vy")


@pytest.fixture(scope="session")
def liquidations_otc_contract_def():
    return boa.load_partial("contracts/LiquidationsOTC.vy")


@pytest.fixture(scope="session")
def liquidity_controls_contract_def():
    return boa.load_partial("contracts/LiquidityControls.vy")


@pytest.fixture(scope="module", autouse=True)
def forked_env():
    old_env = boa.env
    new_env = Env()
    new_env._cached_call_profiles = old_env._cached_call_profiles
    new_env._cached_line_profiles = old_env._cached_line_profiles
    new_env._profiled_contracts = old_env._profiled_contracts

    with boa.swap_env(new_env):
        fork_uri = os.environ["BOA_FORK_RPC_URL"]
        disable_cache = os.environ.get("BOA_FORK_NO_CACHE")
        kw = {"cache_file": None} if disable_cache else {}
        blkid = 17614000
        boa.env.fork(fork_uri, block_identifier=blkid, **kw)
        yield

        old_env._cached_call_profiles = new_env._cached_call_profiles
        old_env._cached_line_profiles = new_env._cached_line_profiles
        old_env._profiled_contracts = new_env._profiled_contracts


@pytest.fixture(scope="module")
def accounts(forked_env):
    _accounts = [boa.env.generate_address() for _ in range(10)]
    for account in _accounts:
        boa.env.set_balance(account, 10**21)
    return _accounts


@pytest.fixture(scope="module")
def owner_account(forked_env):
    return Account.create()


@pytest.fixture(scope="module")
def not_owner_account(forked_env):
    return Account.create()


@pytest.fixture(scope="module", autouse=True)
def contract_owner(accounts, owner_account):
    boa.env.eoa = owner_account.address
    boa.env.set_balance(owner_account.address, 10**21)
    return owner_account.address


@pytest.fixture(scope="module")
def not_contract_owner(not_owner_account):
    return not_owner_account.address


@pytest.fixture(scope="module")
def investor(accounts):
    return accounts[1]


@pytest.fixture(scope="module")
def borrower(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture(scope="module")
def erc20_contract(contract_owner, accounts, erc20_contract_def):
    erc20 = erc20_contract_def.at("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    for account in accounts:
        erc20.deposit(sender=account, value=10**19)
    erc20.deposit(sender=contract_owner, value=10**19)
    return erc20


@pytest.fixture(scope="module")
def usdc_contract(contract_owner, accounts, erc20_contract_def):
    erc20 = erc20_contract_def.at("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    holder = "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1"
    with boa.env.prank(holder):
        for account in accounts:
            erc20.transfer(account, 10**12, sender=holder)
    erc20.transfer(contract_owner, 10**12, sender=holder)
    return erc20


@pytest.fixture(scope="module")
def erc721_contract(contract_owner, erc721_contract_def):
    with boa.env.prank(contract_owner):
        return erc721_contract_def.deploy()


@pytest.fixture(scope="module")
def cryptopunks_market_contract(contract_owner, cryptopunks_market_contract_def):
    return cryptopunks_market_contract_def.at("0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB")


@pytest.fixture(scope="module")
def wpunks_contract(contract_owner, wpunks_contract_def):
    return wpunks_contract_def.at("0xb7F7F6C52F2e2fdb1963Eab30438024864c313F6")


@pytest.fixture(scope="module")
def hashmasks_contract(contract_owner, erc721_contract_def):
    return erc721_contract_def.at("0xC2C747E0F7004F9E8817Db2ca4997657a7746928")


@pytest.fixture(scope="module")
def delegation_registry_contract(contract_owner, delegation_registry_contract_def):
    return delegation_registry_contract_def.at("0x00000000000076A84feF008CDAbe6409d2FE638B")


@pytest.fixture(scope="module")
def genesis_contract(contract_owner, genesis_contract_def):
    return genesis_contract_def.deploy(contract_owner)


@pytest.fixture(scope="module")
def collateral_vault_core_contract(contract_owner, delegation_registry_contract, collateral_vault_core_contract_def):
    with boa.env.prank(contract_owner):
        return collateral_vault_core_contract_def.deploy(delegation_registry_contract)


@pytest.fixture(scope="module")
def cryptopunks_vault_core_contract(cryptopunks_market_contract, delegation_registry_contract, cryptopunks_vault_core_contract_def):
    return cryptopunks_vault_core_contract_def.deploy(cryptopunks_market_contract.address, delegation_registry_contract.address)


@pytest.fixture(scope="module")
def collateral_vault_peripheral_contract(collateral_vault_core_contract, collateral_vault_peripheral_contract_def):
    return collateral_vault_peripheral_contract_def.deploy(collateral_vault_core_contract)


@pytest.fixture(scope="module")
def lending_pool_core_contract(erc20_contract, lending_pool_core_contract_def):
    return lending_pool_core_contract_def.deploy(erc20_contract)


@pytest.fixture(scope="module")
def lending_pool_lock_contract(erc20_contract, lending_pool_lock_contract_def):
    return lending_pool_lock_contract_def.deploy(erc20_contract)


@pytest.fixture(scope="module")
def lending_pool_peripheral_contract(
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    lending_pool_peripheral_contract_def,
    protocol_wallet
):
    return lending_pool_peripheral_contract_def.deploy(
        lending_pool_core_contract,
        lending_pool_lock_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
    )


@pytest.fixture(scope="module")
def usdc_lending_pool_core_contract(usdc_contract, lending_pool_core_contract_def):
    return lending_pool_core_contract_def.deploy(usdc_contract)


@pytest.fixture(scope="module")
def usdc_lending_pool_lock_contract(usdc_contract, lending_pool_lock_contract_def):
    return lending_pool_lock_contract_def.deploy(usdc_contract)


@pytest.fixture(scope="module")
def usdc_lending_pool_peripheral_contract(
    usdc_lending_pool_core_contract,
    usdc_lending_pool_lock_contract,
    usdc_contract,
    lending_pool_peripheral_contract_def,
    protocol_wallet
):
    return lending_pool_peripheral_contract_def.deploy(
        usdc_lending_pool_core_contract,
        usdc_lending_pool_lock_contract,
        usdc_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
    )


@pytest.fixture(scope="module")
def lending_pool_peripheral_contract_aux(
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    lending_pool_peripheral_contract_def,
    protocol_wallet
):
    return lending_pool_peripheral_contract_def.deploy(
        lending_pool_core_contract,
        lending_pool_lock_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
    )


@pytest.fixture(scope="module")
def loans_core_contract(loans_core_contract_def):
    return loans_core_contract_def.deploy()


@pytest.fixture(scope="module")
def loans_peripheral_contract(
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_peripheral_contract,
    genesis_contract,
    loans_peripheral_contract_def
):
    return loans_peripheral_contract_def.deploy(
        INTEREST_ACCRUAL_PERIOD,
        loans_core_contract,
        lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        genesis_contract,
        True,
    )


@pytest.fixture(scope="module")
def usdc_loans_core_contract(loans_core_contract_def):
    return loans_core_contract_def.deploy()


@pytest.fixture(scope="module")
def usdc_loans_peripheral_contract(
    usdc_loans_core_contract,
    usdc_lending_pool_peripheral_contract,
    collateral_vault_peripheral_contract,
    genesis_contract,
    loans_peripheral_contract_def
):
    return loans_peripheral_contract_def.deploy(
        INTEREST_ACCRUAL_PERIOD,
        usdc_loans_core_contract,
        usdc_lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        genesis_contract,
        False,
    )


@pytest.fixture(scope="module")
def liquidations_core_contract(liquidations_core_contract_def):
    return liquidations_core_contract_def.deploy()


@pytest.fixture(scope="module")
def liquidations_peripheral_contract(liquidations_core_contract, erc20_contract, liquidations_peripheral_contract_def):
    liquidations_peripheral_contract = liquidations_peripheral_contract_def.deploy(
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


@pytest.fixture(scope="module")
def liquidity_controls_contract(liquidity_controls_contract_def):
    return liquidity_controls_contract_def.deploy(
        False,
        MAX_POOL_SHARE,
        False,
        LOCK_PERIOD_DURATION,
        False,
        MAX_LOANS_POOL_SHARE,
        False,
    )


@pytest.fixture(scope="module")
def usdc_liquidity_controls_contract(liquidity_controls_contract_def):
    return liquidity_controls_contract_def.deploy(
        False,
        MAX_POOL_SHARE,
        False,
        LOCK_PERIOD_DURATION,
        False,
        MAX_LOANS_POOL_SHARE,
        False,
    )



@pytest.fixture(scope="module")
def test_collaterals(erc721_contract):
    result = []
    for k in range(5):
        result.append((erc721_contract.address, k, LOAN_AMOUNT // 5))
    return result


@pytest.fixture(scope="module")
def cryptopunk_collaterals(cryptopunks_market_contract, borrower):
    result = []
    for k in range(5):
        owner = cryptopunks_market_contract.punkIndexToAddress(k)
        with boa.env.prank(owner):
            cryptopunks_market_contract.transferPunk(borrower, k, sender=owner)
        result.append((cryptopunks_market_contract.address, k, LOAN_AMOUNT // 5))
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
        collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract, sender=contract_owner)
        liquidations_peripheral_contract.setCryptoPunksAddress(cryptopunks_market_contract, sender=contract_owner)
        liquidations_peripheral_contract.setWrappedPunksAddress(wpunks_contract, sender=contract_owner)
        yield


@pytest.fixture(scope="module")
def usdc_contracts_config(
    contracts_config,
    collateral_vault_peripheral_contract,
    contract_owner,
    usdc_contract,
    usdc_lending_pool_core_contract,
    usdc_lending_pool_lock_contract,
    usdc_lending_pool_peripheral_contract,
    liquidations_core_contract,
    liquidations_peripheral_contract,
    usdc_liquidity_controls_contract,
    usdc_loans_core_contract,
    usdc_loans_peripheral_contract,
):
    with boa.env.anchor():
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(usdc_contract, usdc_loans_peripheral_contract, sender=contract_owner)
        usdc_lending_pool_core_contract.setLendingPoolPeripheralAddress(usdc_lending_pool_peripheral_contract, sender=contract_owner)
        usdc_lending_pool_lock_contract.setLendingPoolPeripheralAddress(usdc_lending_pool_peripheral_contract, sender=contract_owner)
        usdc_lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
        usdc_lending_pool_peripheral_contract.setLiquidityControlsAddress(usdc_liquidity_controls_contract, sender=contract_owner)
        usdc_lending_pool_peripheral_contract.setLoansPeripheralAddress(usdc_loans_peripheral_contract, sender=contract_owner)
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(usdc_contract, usdc_lending_pool_peripheral_contract, sender=contract_owner)
        liquidations_peripheral_contract.addLoansCoreAddress(usdc_contract, usdc_loans_core_contract, sender=contract_owner)
        usdc_loans_core_contract.setLoansPeripheral(usdc_loans_peripheral_contract, sender=contract_owner)
        usdc_loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
        usdc_loans_peripheral_contract.setLiquidityControlsAddress(usdc_liquidity_controls_contract, sender=contract_owner)
        yield
