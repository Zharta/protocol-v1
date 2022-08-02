import pytest


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
