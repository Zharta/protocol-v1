import boa
from web3 import Web3
from eth_account import Account
from .conftest_base import get_last_event, ZERO_ADDRESS
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


@pytest.fixture(scope="module", autouse=True)
def forked_env():
    with boa.swap_env(Env()):
        fork_uri = os.environ["BOA_FORK_RPC_URL"]
        blkid = 17614000
        boa.env.fork(fork_uri, block_identifier=blkid)
        yield


@pytest.fixture(scope="session")
def accounts():
    _accounts = [boa.env.generate_address() for _ in range(10)]
    for account in _accounts:
        boa.env.set_balance(account, 10**21)
    return _accounts


@pytest.fixture(scope="session")
def owner_account():
    return Account.create()


@pytest.fixture(scope="session")
def not_owner_account():
    return Account.create()


@pytest.fixture(scope="session", autouse=True)
def contract_owner(accounts, owner_account):
    # boa.env.eoa = accounts[0]  # avoid all the pranks in test setups
    # return accounts[0]
    boa.env.eoa = owner_account.address
    boa.env.set_balance(owner_account.address, 10**21)
    return owner_account.address


@pytest.fixture(scope="session")
def not_contract_owner(not_owner_account):
    return not_owner_account.address


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
    erc20.deposit(sender=contract_owner, value=10**19)
    return erc20


@pytest.fixture(scope="session")
def usdc_contract(contract_owner, accounts):
    erc20 = boa.load_partial("tests/stubs/ERC20.vy").at("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    holder = "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1"
    with boa.env.prank(holder):
        for account in accounts:
            erc20.transfer(account, 10**12, sender=holder)
    erc20.transfer(contract_owner, 10**12, sender=holder)
    return erc20


@pytest.fixture(scope="session")
def erc721_contract(contract_owner):
    return boa.load("contracts/auxiliary/token/ERC721.vy")


@pytest.fixture(scope="session")
def cryptopunks_market_contract(contract_owner):
    return boa.load_partial("tests/stubs/CryptoPunksMarketStub.vy").at("0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB")


@pytest.fixture(scope="session")
def wpunks_contract(contract_owner):
    return boa.load_partial("tests/stubs/WrappedPunkStub.vy").at("0xb7F7F6C52F2e2fdb1963Eab30438024864c313F6")


@pytest.fixture(scope="session")
def hashmasks_contract(contract_owner):
    return boa.load_partial("contracts/auxiliary/token/ERC721.vy").at("0xC2C747E0F7004F9E8817Db2ca4997657a7746928")


@pytest.fixture(scope="session")
def delegation_registry_contract(contract_owner):
    return boa.load_partial("contracts/auxiliary/delegate/DelegationRegistryMock.vy").at("0x00000000000076A84feF008CDAbe6409d2FE638B")


@pytest.fixture(scope="session")
def genesis_contract(contract_owner):
    return boa.load("contracts/GenesisPass.vy", contract_owner)


@pytest.fixture(scope="session")
def collateral_vault_core_contract(contract_owner, delegation_registry_contract):
    with boa.env.prank(contract_owner):
        return boa.load("contracts/CollateralVaultCoreV2.vy", delegation_registry_contract)

@pytest.fixture(scope="session")
def cryptopunks_vault_core_contract(cryptopunks_market_contract, delegation_registry_contract, contract_owner):
    return boa.load("contracts/CryptoPunksVaultCore.vy", cryptopunks_market_contract.address, delegation_registry_contract.address)


@pytest.fixture(scope="session")
def collateral_vault_peripheral_contract(collateral_vault_core_contract, contract_owner):
    return boa.load("contracts/CollateralVaultPeripheral.vy", collateral_vault_core_contract)


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
def usdc_lending_pool_core_contract(usdc_contract, contract_owner):
    return boa.load("contracts/LendingPoolCore.vy", usdc_contract)


@pytest.fixture(scope="session")
def usdc_lending_pool_lock_contract(usdc_contract, contract_owner):
    return boa.load("contracts/LendingPoolLock.vy", usdc_contract)


@pytest.fixture(scope="session")
def usdc_lending_pool_peripheral_contract(usdc_lending_pool_core_contract, usdc_lending_pool_lock_contract, usdc_contract, contract_owner, protocol_wallet):
    return boa.load(
        "contracts/LendingPoolPeripheral.vy",
        usdc_lending_pool_core_contract,
        usdc_lending_pool_lock_contract,
        usdc_contract,
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
def loans_core_contract(contract_owner):
    return boa.load("contracts/LoansCore.vy")


@pytest.fixture(scope="session")
def loans_peripheral_contract(loans_core_contract, lending_pool_peripheral_contract, collateral_vault_peripheral_contract, genesis_contract, contract_owner):
    return boa.load(
        "contracts/Loans.vy",
        INTEREST_ACCRUAL_PERIOD,
        loans_core_contract,
        lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        genesis_contract,
    )


@pytest.fixture(scope="session")
def usdc_loans_core_contract(contract_owner):
    return boa.load("contracts/LoansCore.vy")


@pytest.fixture(scope="session")
def usdc_loans_peripheral_contract(usdc_loans_core_contract, usdc_lending_pool_peripheral_contract, collateral_vault_peripheral_contract, genesis_contract, contract_owner):
    return boa.load(
        "contracts/Loans.vy",
        INTEREST_ACCRUAL_PERIOD,
        usdc_loans_core_contract,
        usdc_lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        genesis_contract,
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
def usdc_liquidity_controls_contract(contract_owner):
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



# @pytest.fixture(scope="module", autouse=True)
# def sushi_router_contract(contract_owner):
#     abi = """ [
#     {
#         "inputs": [
#           {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
#           {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
#           {"internalType": "address[]", "name": "path", "type": "address[]"},
#           {"internalType": "address", "name": "to", "type": "address"},
#           {"internalType": "uint256", "name": "deadline", "type": "uint256"}
#         ],
#         "name": "swapExactTokensForTokens",
#         "outputs": [
#           {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
#         ],
#         "stateMutability": "nonpayable",
#         "type": "function"
#       }
#     ] """
#     return Contract.from_abi(
#         "SushiRouter",
#         "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
#         json.loads(abi),
#         owner=contract_owner
#     )



@pytest.fixture(scope="session")
def test_collaterals(erc721_contract):
    result = []
    for k in range(5):
        result.append((erc721_contract.address, k, LOAN_AMOUNT // 5))
    return result


@pytest.fixture(scope="session")
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
