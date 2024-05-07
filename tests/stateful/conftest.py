import boa
import pytest
from eth_account import Account


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
    boa.env.eoa = owner_account.address
    boa.env.set_balance(owner_account.address, 10**21)
    return owner_account.address


@pytest.fixture(scope="session")
def not_contract_owner(not_owner_account):
    return not_owner_account.address


@pytest.fixture(scope="session")  # noqa: FURB118
def investor(accounts):
    return accounts[1]


@pytest.fixture(scope="session")
def borrower(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def erc721_contract(contract_owner):
    return boa.load("contracts/auxiliary/token/ERC721.vy")


@pytest.fixture(scope="session")
def lendingpool_eth_otc_contract():
    return boa.load_partial("contracts/LendingPoolEthOTC.vy")


@pytest.fixture(scope="session")
def lendingpool_erc20_otc_contract():
    return boa.load_partial("contracts/LendingPoolERC20OTC.vy")


@pytest.fixture(scope="session")
def weth9_contract():
    return boa.load_partial("contracts/auxiliary/token/WETH9Mock.vy")
