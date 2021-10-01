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
def inv_pool_contract(InvestmentPool, contract_owner):
    yield InvestmentPool.deploy(contract_owner, {'from': contract_owner})


def test_initial_state(inv_pool_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert inv_pool_contract.owner() == contract_owner
    assert inv_pool_contract.loansContract() == contract_owner


def test_invest_zero_investment(inv_pool_contract, investor):
    with brownie.reverts("Amount invested has to be higher than 0!"):
        inv_pool_contract.invest({"from": investor, "value": "0 ether"})


def test_invest(inv_pool_contract, investor):
    tx = inv_pool_contract.invest({"from": investor, "value": "1 ether"})

    funds_from_address = tx.return_value

    assert funds_from_address["totalAmountInvested"] == Web3.toWei(1, "ether")
    assert funds_from_address["currentAmountInvested"] == Web3.toWei(1, "ether")
    assert inv_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    assert len(tx.events) == 1
    assert tx.events[0]["_from"] == investor
    assert tx.events[0]["amount"] == Web3.toWei(1, "ether")


def test_invest_twice(inv_pool_contract, investor):
    inv_pool_contract.invest({"from": investor, "value": "1 ether"})
    inv_pool_contract.invest({"from": investor, "value": "0.5 ether"})

    funds_from_address = inv_pool_contract.fundsFromAddress(investor, {"from": investor})

    assert funds_from_address["totalAmountInvested"] == Web3.toWei(1.5, "ether")
    assert funds_from_address["currentAmountInvested"] == Web3.toWei(1.5, "ether")
    assert inv_pool_contract.fundsAvailable() == Web3.toWei(1.5, "ether")


def test_withdraw_noinvestment(inv_pool_contract, investor):
    with brownie.reverts("The sender has no funds invested!"):
        inv_pool_contract.withdrawFunds(Web3.toWei(1, "ether"), {"from": investor})


def test_withdraw_insufficient_investment(inv_pool_contract, investor):
    inv_pool_contract.invest({"from": investor, "value": "0.5 ether"})
    
    with brownie.reverts("The sender has less funds invested than the amount requested!"):
        inv_pool_contract.withdrawFunds(Web3.toWei(1, "ether"), {"from": investor})


def test_withdraw(inv_pool_contract, investor):
    initial_balance = investor.balance()
    
    tx_invest = inv_pool_contract.invest({"from": investor, "value": "1 ether"})
    assert investor.balance() == initial_balance - Web3.toWei(1, "ether")
    assert inv_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    tx_withdraw = inv_pool_contract.withdrawFunds(Web3.toWei(1, "ether"), {"from": investor})
    assert investor.balance() == initial_balance
    assert inv_pool_contract.fundsAvailable() == 0

    funds_from_address = inv_pool_contract.fundsFromAddress(investor, {"from": investor})

    assert funds_from_address["totalAmountInvested"] == Web3.toWei(1, "ether")
    assert funds_from_address["currentAmountInvested"] == 0
    assert funds_from_address["totalAmountWithdrawn"] == Web3.toWei(1, "ether")

    assert len(tx_withdraw.events) == 1
    assert tx_withdraw.events[0]["_from"] == investor
    assert tx_withdraw.events[0]["amount"] == Web3.toWei(1, "ether")


def test_send_funds_wrong_sender(inv_pool_contract, investor, borrower):
    with brownie.reverts("The sender's address is not the loans contract address!"):
        inv_pool_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": investor})


def test_send_funds_zero_amount(inv_pool_contract, contract_owner, borrower):
    with brownie.reverts("The amount to send should be higher than 0!"):
        inv_pool_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": contract_owner}
        )


def test_send_funds_wrong_amount(inv_pool_contract, contract_owner, investor, borrower):
    inv_pool_contract.invest({"from": investor, "value": "1 ether"})
    with brownie.reverts("No sufficient invested funds to perform the transaction!"):
        inv_pool_contract.sendFunds(
            borrower,
            Web3.toWei(2, "ether"),
            {"from": contract_owner}
        )


def test_send_funds(inv_pool_contract, contract_owner, investor, borrower):
    initial_balance = borrower.balance()
    
    tx_invest = inv_pool_contract.invest({"from": investor, "value": "1 ether"})
    tx_send = inv_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    assert borrower.balance() == initial_balance + Web3.toWei(0.2, "ether")
    assert inv_pool_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert inv_pool_contract.fundsInvested() == Web3.toWei(0.2, "ether")

    assert len(tx_send.events) == 1
    assert tx_send.events[0]["_to"] == borrower
    assert tx_send.events[0]["amount"] == Web3.toWei(0.2, "ether")


def test_receive_funds_wrong_sender(inv_pool_contract, borrower):
    with brownie.reverts("The sender's address is not the loans contract address!"):
        inv_pool_contract.receiveFunds(
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower, "value": "0.25 ether"}
        )


def test_receive_funds_wrong_sum(inv_pool_contract, contract_owner):
    with brownie.reverts("The sent value is different than the sum of _amount and _interestAmount!"):
        inv_pool_contract.receiveFunds(
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": contract_owner, "value": "0.5 ether"}
        )


def test_receive_funds_zero_value(inv_pool_contract, contract_owner):
    with brownie.reverts("The sent value should be higher than 0!"):
        inv_pool_contract.receiveFunds(
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": contract_owner, "value": "0 ether"}
        )


def test_receive_funds(inv_pool_contract, contract_owner, investor, borrower):
    tx_invest = inv_pool_contract.invest({"from": investor, "value": "1 ether"})
    
    tx_send = inv_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    tx_receive = inv_pool_contract.receiveFunds(
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": contract_owner, "value": "0.22 ether"}
    )

    assert inv_pool_contract.fundsAvailable() == Web3.toWei(1.02, "ether")
    assert inv_pool_contract.fundsInvested() == 0
    assert inv_pool_contract.totalRewards() == Web3.toWei(0.02, "ether")

    assert len(tx_receive.events) == 1
    assert tx_receive.events[0]["_from"] == contract_owner
    assert tx_receive.events[0]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events[0]["interestAmount"] == Web3.toWei(0.02, "ether")

