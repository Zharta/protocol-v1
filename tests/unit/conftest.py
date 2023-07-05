import boa
from web3 import Web3
from eth_account import Account
from ..conftest_base import get_last_event, ZERO_ADDRESS
from datetime import datetime as dt
from boa.environment import Env

import pytest
import os


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
def erc721_contract(contract_owner):
    return boa.load("contracts/auxiliary/token/ERC721.vy")
