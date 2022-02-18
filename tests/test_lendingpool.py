from brownie.network import chain
from datetime import datetime as dt
from decimal import Decimal
from web3 import Web3

import brownie
import pytest


MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000


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
    yield LendingPool.deploy(contract_owner, erc20_contract, MAX_CAPITAL_EFFICIENCY, {'from': contract_owner})


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)


def test_initial_state(lending_pool_contract, erc20_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_contract.owner() == contract_owner
    assert lending_pool_contract.loansContract() == contract_owner
    assert lending_pool_contract.erc20TokenContract() == erc20_contract


def test_deposit_zero_investment(lending_pool_contract, investor):
    with brownie.reverts("Amount deposited has to be higher than 0"):
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
    
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    funds_from_address = tx_deposit.return_value

    assert funds_from_address["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert funds_from_address["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert funds_from_address["totalAmountWithdrawn"] == 0
    assert funds_from_address["currentPendingRewards"] == 0
    assert funds_from_address["totalRewardsAmount"] == 0
    assert funds_from_address["activeForRewards"] == True
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    assert len(tx_deposit.events) == 3
    assert tx_deposit.events[-1]["_from"] == investor
    assert tx_deposit.events[-1]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events[-1]["erc20TokenContract"] == erc20_contract


def test_deposit_twice(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    tx_deposit_twice = lending_pool_contract.deposit(Web3.toWei(0.5, "ether"), {"from": investor})

    funds_from_address = tx_deposit_twice.return_value

    assert funds_from_address["currentAmountDeposited"] == Web3.toWei(1.5, "ether")
    assert funds_from_address["totalAmountDeposited"] == Web3.toWei(1.5, "ether")
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1.5, "ether")


def test_withdraw_noinvestment(lending_pool_contract, investor):
    with brownie.reverts("The sender has no funds deposited"):
        lending_pool_contract.withdraw(Web3.toWei(1, "ether"), {"from": investor})


def test_withdraw_insufficient_investment(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("The sender has less funds deposited than the amount requested"):
        lending_pool_contract.withdraw(Web3.toWei(1.5, "ether"), {"from": investor})


def test_withdraw(lending_pool_contract, erc20_contract, investor, contract_owner):
    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(2, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    tx_withdraw = lending_pool_contract.withdraw(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")
    assert lending_pool_contract.fundsAvailable() == 0

    funds_from_address = tx_withdraw.return_value
    assert funds_from_address["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert funds_from_address["currentAmountDeposited"] == 0
    assert funds_from_address["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert funds_from_address["currentPendingRewards"] == 0
    assert funds_from_address["activeForRewards"] == False

    assert len(tx_withdraw.events) == 3
    assert tx_withdraw.events[-1]["_from"] == investor
    assert tx_withdraw.events[-1]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events[-1]["erc20TokenContract"] == erc20_contract


def test_send_funds_wrong_sender(lending_pool_contract, investor, borrower):
    with brownie.reverts("Only the loans contract address can request to send funds"):
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
    
    print(lending_pool_contract.hasFundsToInvest())
    print(lending_pool_contract.maxFundsInvestable())
    print(lending_pool_contract.isPoolInvesting())
    print(lending_pool_contract.isPoolActive())

    with brownie.reverts("No sufficient deposited funds to perform the transaction"):
        lending_pool_contract.sendFunds(
            borrower,
            Web3.toWei(2, "ether"),
            {"from": contract_owner}
        )


def test_send_funds_insufficient_funds_to_lend(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("No sufficient deposited funds to perform the transaction"):
        tx_send = lending_pool_contract.sendFunds(
            borrower,
            Web3.toWei(0.8, "ether"),
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
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
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

    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_contract.fundsInvested() == 0
    assert lending_pool_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")
    
    assert lending_pool_contract.totalRewards() == Web3.toWei(0.02, "ether")

    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == Web3.toWei(0.02, "ether")
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(0.02, "ether")

    assert len(tx_receive.events) == 3
    assert tx_receive.events[-1]["_from"] == contract_owner
    assert tx_receive.events[-1]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events[-1]["interestAmount"] == Web3.toWei(0.02, "ether")
    assert tx_send.events[-1]["erc20TokenContract"] == erc20_contract


def test_receive_funds_multiple_lenders(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    erc20_contract.mint(contract_owner, Web3.toWei(3, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(3, "ether"), {"from": contract_owner})
    lending_pool_contract.deposit(Web3.toWei(3, "ether"), {"from": contract_owner})

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

    assert lending_pool_contract.fundsAvailable() == Web3.toWei(4, "ether")
    assert lending_pool_contract.fundsInvested() == 0
    assert lending_pool_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")
    
    assert lending_pool_contract.totalRewards() == Web3.toWei(0.02, "ether")

    expectedLenderOneRewards = Decimal(0.02) * Decimal(1) / Decimal(4)
    expectedLenderTwoRewards = Decimal(0.02) * Decimal(3) / Decimal(4)

    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == Web3.toWei(expectedLenderOneRewards, "ether")
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(expectedLenderOneRewards, "ether")
    assert lending_pool_contract.funds(contract_owner)["currentPendingRewards"] == Web3.toWei(expectedLenderTwoRewards, "ether")
    assert lending_pool_contract.funds(contract_owner)["totalRewardsAmount"] == Web3.toWei(expectedLenderTwoRewards, "ether")

    assert len(tx_receive.events) == 3
    assert tx_receive.events[-1]["_from"] == contract_owner
    assert tx_receive.events[-1]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events[-1]["interestAmount"] == Web3.toWei(0.02, "ether")
    assert tx_send.events[-1]["erc20TokenContract"] == erc20_contract


def test_compound_rewards_no_deposits(lending_pool_contract, investor):
    with brownie.reverts("The sender has no funds deposited"):
        lending_pool_contract.compoundRewards({"from": investor})


def test_compound_rewards_no_pending_rewards(lending_pool_contract, erc20_contract, contract_owner, investor):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("The sender has no pending rewards to compound"):
        lending_pool_contract.compoundRewards({"from": investor})    


def test_compound_rewards(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
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

    tx_compound = lending_pool_contract.compoundRewards({"from": investor})

    assert lending_pool_contract.funds(investor)["currentAmountDeposited"] == Web3.toWei(1.02, "ether")
    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == 0
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(0.02, "ether")
    assert lending_pool_contract.funds(investor)["activeForRewards"] == True

    assert tx_compound.events[-1]["_from"] == investor
    assert tx_compound.events[-1]["rewards"] == Web3.toWei(0.02, "ether")
    assert tx_compound.events[-1]["erc20TokenContract"] == erc20_contract


def test_rewards_computation(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
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

    init_of_day = int(dt.today().timestamp()) - int(dt.today().timestamp()) % 86400
    assert lending_pool_contract.days(0) == init_of_day
    assert lending_pool_contract.rewardsByDay(init_of_day) == Web3.toWei(0.02, "ether")


def test_rewards_computation_over_two_days(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
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

    init_of_day_one = int(dt.today().timestamp()) - int(dt.today().timestamp()) % 86400
    assert lending_pool_contract.days(0) == init_of_day_one
    assert lending_pool_contract.rewardsByDay(init_of_day_one) == Web3.toWei(0.02, "ether")

    # ADVANCE TIME 1 DAY
    chain.mine(timedelta=86400)

    tx_send = lending_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.3, "ether"),
        {"from": contract_owner}
    )

    erc20_contract.mint(borrower, Web3.toWei(0.33, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.33, "ether"), {"from": borrower})

    tx_receive = lending_pool_contract.receiveFunds(
        borrower,
        Web3.toWei(0.3, "ether"),
        Web3.toWei(0.03, "ether"),
        {"from": contract_owner}
    )

    init_of_day_two = init_of_day_one + 86400
    
    assert lending_pool_contract.days(0) == init_of_day_one
    assert lending_pool_contract.days(1) == init_of_day_two
    assert lending_pool_contract.rewardsByDay(init_of_day_one) == Web3.toWei(0.02, "ether")
    assert lending_pool_contract.rewardsByDay(init_of_day_two) == Web3.toWei(0.03, "ether")


def test_rewards_computation_over_eight_days(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    chain.mine(timedelta=86400)

    chain_time = chain.time()
    initial_day_timestamp = chain_time - chain_time % 86400

    for day in range(0, 9):
        # ADVANCE TIME
        if day > 0:
            chain.mine(timedelta=86400)

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

        if day < 7:
            print(day)
            print(lending_pool_contract.days(day))

        if day in [7, 8]:
            init_of_day = initial_day_timestamp + 86400 * day
            print(day - 7)
            print(lending_pool_contract.days(day - 7))
            assert lending_pool_contract.days(day - 7) == init_of_day
            assert lending_pool_contract.rewardsByDay(init_of_day) == Web3.toWei(0.02, "ether")
            assert lending_pool_contract.lastDaysApr(7) / 10**18 == 0.02 * 7 * 365 / 7




