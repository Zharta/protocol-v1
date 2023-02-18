import pytest
from web3 import Web3


@pytest.fixture(scope="module", autouse=True)
def contract_owner(accounts):
    # owner = accounts["0xbb4b8e7e4375d27f27518ac7f8c6db473fdc3a10a42389cf984c87bc7a1fce1b"]
    # accounts[0].transfer(owner, 8*10**20)
    return accounts[0]


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
    return accounts[4]

@pytest.fixture(scope="module", autouse=True)
def erc20_contract(project, contract_owner, borrower, investor):
    try:
        _erc20 = project.WETH9Mock.at("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        _erc20.transfer(contract_owner, 100 * 10**18, sender=_erc20)
        _erc20.transfer(borrower, 100 * 10**18, sender=_erc20)
        _erc20.transfer(investor, 100 * 10**18, sender=_erc20)
    except Exception:
        _erc20 = contract_owner.deploy(project.WETH9Mock, "WrappedEther", "WETH", 18, 1000 * 10 ** 18)
        _erc20.transfer(contract_owner, 100 * 10**18, sender=contract_owner)
        _erc20.transfer(borrower, 100 * 10**18, sender=contract_owner)
        _erc20.transfer(investor, 100 * 10**18, sender=contract_owner)
    return _erc20


@pytest.fixture(scope="module", autouse=True)
def erc721_contract(project, contract_owner):
    yield contract_owner.deploy(project.ERC721)
