from datetime import datetime as dt
from web3 import Web3

import conftest_base
import pytest


MAX_NUMBER_OF_LOANS = 10
MAX_LOAN_DURATION = 31 * 24 * 60 * 60 # 31 days
MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000
MAX_LOAN_AMOUNT = Web3.toWei(3, "ether")
INTEREST_ACCRUAL_PERIOD = 24 * 60 * 60

PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000

GRACE_PERIOD_DURATION = 50 # 2 days
LENDER_PERIOD_DURATION = 50 # 15 days
AUCTION_DURATION = 50 # 15 days

MAX_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_LOANS_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_COLLECTION_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


contract_owner = conftest_base.contract_owner
not_contract_owner = conftest_base.not_contract_owner
investor = conftest_base.investor
borrower = conftest_base.borrower
protocol_wallet = conftest_base.protocol_wallet
erc20_contract = conftest_base.erc20_contract
erc721_contract = conftest_base.erc721_contract


@pytest.fixture(scope="module", autouse=True)
def collateral_vault_core_contract(CollateralVaultCore, contract_owner):
    yield CollateralVaultCore.deploy({"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def collateral_vault_peripheral_contract(CollateralVaultPeripheral, collateral_vault_core_contract, contract_owner):
    yield CollateralVaultPeripheral.deploy(collateral_vault_core_contract, {"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def lending_pool_core_contract(LendingPoolCore, erc20_contract, contract_owner):
    yield LendingPoolCore.deploy(erc20_contract, {'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def lending_pool_peripheral_contract(LendingPoolPeripheral, lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolPeripheral.deploy(
        lending_pool_core_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def lending_pool_peripheral_contract_aux(LendingPoolPeripheral, lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolPeripheral.deploy(
        lending_pool_core_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def loans_peripheral_contract(Loans, loans_core_contract, lending_pool_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    yield Loans.deploy(
        MAX_NUMBER_OF_LOANS,
        MAX_LOAN_DURATION,
        MAX_LOAN_AMOUNT,
        INTEREST_ACCRUAL_PERIOD,
        loans_core_contract,
        lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def loans_peripheral_contract_aux(Loans, lending_pool_peripheral_contract, contract_owner, accounts):
    yield Loans.deploy(
        1,
        1,
        1,
        INTEREST_ACCRUAL_PERIOD,
        accounts[4],
        lending_pool_peripheral_contract,
        accounts[5],
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def liquidations_core_contract(LiquidationsCore, contract_owner):
    yield LiquidationsCore.deploy({"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def liquidations_peripheral_contract(LiquidationsPeripheral, liquidations_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract = LiquidationsPeripheral.deploy(
        liquidations_core_contract,
        GRACE_PERIOD_DURATION,
        LENDER_PERIOD_DURATION,
        AUCTION_DURATION,
        erc20_contract,
        {"from": contract_owner}
    )
    liquidations_peripheral_contract.setNFTXVaultFactoryAddress("0xBE86f647b167567525cCAAfcd6f881F1Ee558216", {"from": contract_owner})
    liquidations_peripheral_contract.setNFTXMarketplaceZapAddress("0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d", {"from": contract_owner})
    liquidations_peripheral_contract.setSushiRouterAddress("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", {"from": contract_owner})
    return liquidations_peripheral_contract


@pytest.fixture(scope="module", autouse=True)
def liquidity_controls_contract(LiquidityControls, contract_owner):
    yield LiquidityControls.deploy(
        False,
        MAX_POOL_SHARE,
        False,
        LOCK_PERIOD_DURATION,
        False,
        MAX_LOANS_POOL_SHARE,
        False,
        MAX_COLLECTION_SHARE,
        {"from": contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def test_collaterals(erc721_contract):
    result = []
    for k in range(5):
        result.append((erc721_contract.address, k, LOAN_AMOUNT / 5))
    yield result


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
