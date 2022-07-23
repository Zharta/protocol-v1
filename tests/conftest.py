from web3 import Web3

import pytest


GRACE_PERIOD_DURATION = 172800 # 2 days
BUY_NOW_PERIOD_DURATION = 604800 # 15 days
AUCTION_DURATION = 604800 # 15 days

PRINCIPAL = Web3.toWei(1, "ether")
INTEREST_AMOUNT = Web3.toWei(0.1, "ether")
APR = 200


@pytest.fixture(scope="module", autouse=True)
def contract_owner(accounts):
    yield accounts[0]


@pytest.fixture(scope="module", autouse=True)
def borrower(accounts):
    yield accounts[1]


@pytest.fixture(scope="module", autouse=True)
def collateral_vault_contract(accounts):
    yield accounts[2]


@pytest.fixture(scope="module", autouse=True)
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def erc721_contract(ERC721, contract_owner):
    yield ERC721.deploy({'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


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
def buy_now_core_contract(BuyNowCore, contract_owner):
    yield BuyNowCore.deploy({"from": contract_owner})


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass