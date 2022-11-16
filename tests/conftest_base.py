import pytest
from web3 import Web3



@pytest.fixture(scope="module", autouse=True)
def contract_owner(accounts, gas):
    owner = accounts.add('0xbb4b8e7e4375d27f27518ac7f8c6db473fdc3a10a42389cf984c87bc7a1fce1b')
    accounts[0].transfer(owner, Web3.toWei(800, "ether"))
    return owner


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
def not_contract_owner(accounts):
    return accounts.add()

@pytest.fixture(scope="module", autouse=True)
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def erc721_contract(ERC721, contract_owner):
    yield ERC721.deploy({'from': contract_owner})
