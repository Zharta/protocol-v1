import pytest
import brownie

from web3 import Web3


@pytest.fixture
def contract_owner(accounts):
    yield accounts[0]


@pytest.fixture
def borrower(accounts):
    yield accounts[1]


@pytest.fixture
def investor(accounts):
    yield accounts[2]


@pytest.fixture
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("USD Coin", "USDC", {'from': contract_owner})


@pytest.fixture
def inv_pool_contract(InvestmentPoolV2, erc20_contract, contract_owner):
    yield InvestmentPoolV2.deploy(contract_owner, erc20_contract, {'from': contract_owner})


def test_initial_state(inv_pool_contract, erc20_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert inv_pool_contract.owner() == contract_owner
    assert inv_pool_contract.loansContract() == contract_owner
    assert inv_pool_contract.erc20TokenContract() == erc20_contract


