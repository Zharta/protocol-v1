from datetime import datetime as dt
from web3 import Web3

import pytest


MAX_NUMBER_OF_LOANS = 10
MAX_LOAN_DURATION = 31 * 24 * 60 * 60 # 31 days
MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000
MIN_LOAN_AMOUNT = Web3.toWei(0.05, "ether")
MAX_LOAN_AMOUNT = Web3.toWei(3, "ether")

PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000

GRACE_PERIOD_DURATION = 5 # 2 days
BUY_NOW_PERIOD_DURATION = 5 # 15 days
AUCTION_DURATION = 5 # 15 days


@pytest.fixture(scope="module", autouse=True)
def contract_owner(accounts):
    yield accounts[0]


@pytest.fixture(scope="module", autouse=True)
def investor(accounts):
    yield accounts[1]


@pytest.fixture(scope="module", autouse=True)
def borrower(accounts):
    yield accounts[2]


@pytest.fixture(scope="module", autouse=True)
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture(scope="module", autouse=True)
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def erc721_contract(ERC721, contract_owner):
    yield ERC721.deploy({'from': contract_owner})


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
        MIN_LOAN_AMOUNT,
        MAX_LOAN_AMOUNT,
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
        0,
        1,
        accounts[4],
        lending_pool_peripheral_contract,
        accounts[5],
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def buy_now_core_contract(BuyNowCore, contract_owner):
    yield BuyNowCore.deploy({"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def buy_now_peripheral_contract(BuyNowPeripheral, buy_now_core_contract, erc20_contract, contract_owner):
    yield BuyNowPeripheral.deploy(
        buy_now_core_contract,
        GRACE_PERIOD_DURATION,
        BUY_NOW_PERIOD_DURATION,
        AUCTION_DURATION,
        erc20_contract,
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