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
def erc20_contract(ERC20PresetMinterPauser, contract_owner):
    yield ERC20PresetMinterPauser.deploy("USD Coin", "USDC", {'from': contract_owner})


@pytest.fixture
def lending_pool_contract(LendingPool, erc20_contract, contract_owner):
    yield LendingPool.deploy(contract_owner, erc20_contract, {'from': contract_owner})


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)


def test_initial_state(lending_pool_contract, erc20_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_contract.owner() == contract_owner
    assert lending_pool_contract.loansContract() == contract_owner
    assert lending_pool_contract.erc20TokenContract() == erc20_contract


def test_invest_zero_investment(lending_pool_contract, investor):
    with brownie.reverts("Amount invested has to be higher than 0"):
        lending_pool_contract.deposit(0, {"from": investor})


def test_amount_not_allowed(lending_pool_contract, erc20_contract, investor):
    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})


def test_insufficient_amount_allowed(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    
    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})


def test_deposit(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    funds_from_address = tx_invest.return_value

    assert funds_from_address["currentAmountInvested"] == Web3.toWei(1, "ether")
    assert funds_from_address["totalAmountInvested"] == Web3.toWei(1, "ether")
    assert funds_from_address["totalAmountWithdrawn"] == 0
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    assert len(tx_invest.events) == 3
    assert tx_invest.events[-1]["_from"] == investor
    assert tx_invest.events[-1]["amount"] == Web3.toWei(1, "ether")
    assert tx_invest.events[-1]["erc20TokenContract"] == erc20_contract


def test_deposit_twice(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    tx_invest_twice = lending_pool_contract.deposit(Web3.toWei(0.5, "ether"), {"from": investor})

    funds_from_address = lending_pool_contract.userFunds(investor)

    assert funds_from_address["currentAmountInvested"] == Web3.toWei(1.5, "ether")
    assert funds_from_address["totalAmountInvested"] == Web3.toWei(1.5, "ether")
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1.5, "ether")


def test_withdraw_noinvestment(lending_pool_contract, investor):
    with brownie.reverts("The sender has no funds invested"):
        lending_pool_contract.withdraw(Web3.toWei(1, "ether"), {"from": investor})


def test_withdraw_insufficient_investment(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("The sender has less funds invested than the amount requested"):
        lending_pool_contract.withdraw(Web3.toWei(1.5, "ether"), {"from": investor})


def test_withdraw(lending_pool_contract, erc20_contract, investor, contract_owner):
    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(2, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    print(lending_pool_contract.userFunds(investor))
    
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    tx_withdraw = lending_pool_contract.withdraw(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")
    assert lending_pool_contract.fundsAvailable() == 0

    funds_from_address = lending_pool_contract.userFunds(investor)
    print(tx_withdraw.return_value)
    print(funds_from_address)
    assert funds_from_address["totalAmountInvested"] == Web3.toWei(1, "ether")
    assert funds_from_address["currentAmountInvested"] == 0
    assert funds_from_address["totalAmountWithdrawn"] == Web3.toWei(1, "ether")

    assert len(tx_withdraw.events) == 2
    assert tx_withdraw.events[-1]["_from"] == investor
    assert tx_withdraw.events[-1]["amount"] == Web3.toWei(1, "ether")
    assert tx_withdraw.events[-1]["rewards"] == Web3.toWei(0, "ether")
    assert tx_invest.events[-1]["erc20TokenContract"] == erc20_contract


def test_send_funds_wrong_sender(lending_pool_contract, investor, borrower):
    with brownie.reverts("The sender's address is not the loans contract address"):
        lending_pool_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": investor})


def test_send_funds_zero_amount(lending_pool_contract, contract_owner, borrower):
    with brownie.reverts("The amount to send should be higher than 0"):
        lending_pool_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": contract_owner}
        )


def test_send_funds_wrong_amount(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("No sufficient invested funds to perform the transaction"):
        lending_pool_contract.sendFunds(
            borrower,
            Web3.toWei(2, "ether"),
            {"from": contract_owner}
        )


def test_send_funds(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    initial_balance = user_balance(erc20_contract, borrower)
    
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    tx_send = lending_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_contract.fundsInvested() == Web3.toWei(0.2, "ether")

    assert len(tx_send.events) == 2
    assert tx_send.events[-1]["_to"] == borrower
    assert tx_send.events[-1]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_send.events[-1]["erc20TokenContract"] == erc20_contract


def test_receive_funds_wrong_sender(lending_pool_contract, borrower):
    with brownie.reverts("The sender's address is not the loans contract address"):
        lending_pool_contract.receiveFunds(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower}
        )


def test_receive_funds_insufficient_amount(lending_pool_contract, contract_owner, borrower):
    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_contract.receiveFunds(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": contract_owner}
        )


def test_receive_funds_zero_value(lending_pool_contract, contract_owner, borrower):
    with brownie.reverts("The sent value should be higher than 0"):
        lending_pool_contract.receiveFunds(
            borrower,
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": contract_owner}
        )


def test_receive_funds(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    tx_send = lending_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    erc20_contract.mint(borrower, Web3.toWei(0.22, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.22, "ether"), {"from": borrower})

    tx_receive = lending_pool_contract.receiveFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": contract_owner}
    )

    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1.02, "ether")
    assert lending_pool_contract.fundsInvested() == 0
    assert lending_pool_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")
    
    assert lending_pool_contract.totalRewards() == Web3.toWei(0.02, "ether")
    assert lending_pool_contract.rewards() == Web3.toWei(0.02, "ether")

    assert len(tx_receive.events) == 3
    assert tx_receive.events[-1]["_from"] == contract_owner
    assert tx_receive.events[-1]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events[-1]["interestAmount"] == Web3.toWei(0.02, "ether")
    assert tx_send.events[-1]["erc20TokenContract"] == erc20_contract
