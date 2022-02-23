from brownie.network import chain
from datetime import datetime as dt
from decimal import Decimal
from web3 import Web3

import brownie
import pytest


PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
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
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture
def erc20_contract(ERC20PresetMinterPauser, contract_owner):
    yield ERC20PresetMinterPauser.deploy("USD Coin", "USDC", {'from': contract_owner})


@pytest.fixture
def lending_pool_contract(LendingPool, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPool.deploy(
        contract_owner,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        {'from': contract_owner}
    )


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)


def test_initial_state(lending_pool_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_contract.owner() == contract_owner
    assert lending_pool_contract.loansContract() == contract_owner
    assert lending_pool_contract.erc20TokenContract() == erc20_contract
    assert lending_pool_contract.protocolWallet() == protocol_wallet
    assert lending_pool_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE
    assert lending_pool_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY
    assert lending_pool_contract.isPoolActive() == True
    assert lending_pool_contract.isPoolDeprecated() == False
    assert lending_pool_contract.isPoolInvesting() == False


def test_change_pool_status_wrong_sender(lending_pool_contract, borrower):
    with brownie.reverts("Only the owner can change the pool status"):
        lending_pool_contract.changePoolStatus(False, {"from": borrower})


def test_change_pool_status_same_status(lending_pool_contract, contract_owner):
    with brownie.reverts("The new pool status should be different than the current status"):
        lending_pool_contract.changePoolStatus(True, {"from": contract_owner})


def test_change_pool_status(lending_pool_contract, contract_owner):
    tx = lending_pool_contract.changePoolStatus(False, {"from": contract_owner})

    assert lending_pool_contract.isPoolActive() == False
    assert lending_pool_contract.isPoolInvesting() == False
    assert tx.return_value == lending_pool_contract.isPoolActive()


def test_change_pool_status_again(lending_pool_contract, contract_owner):
    lending_pool_contract.changePoolStatus(False, {"from": contract_owner})

    tx = lending_pool_contract.changePoolStatus(True, {"from": contract_owner})

    assert lending_pool_contract.isPoolActive() == True
    assert lending_pool_contract.isPoolInvesting() == False
    assert tx.return_value == lending_pool_contract.isPoolActive()


def test_deprecate_wrong_sender(lending_pool_contract, borrower):
    with brownie.reverts("Only the owner can change the pool to deprecated"):
        lending_pool_contract.deprecate({"from": borrower})


def test_deprecate(lending_pool_contract, contract_owner):
    tx = lending_pool_contract.deprecate({"from": contract_owner})

    assert lending_pool_contract.isPoolDeprecated() == True
    assert lending_pool_contract.isPoolActive() == False
    assert lending_pool_contract.isPoolInvesting() == False
    assert tx.return_value == lending_pool_contract.isPoolDeprecated()


def test_deprecate_already_deprecated(lending_pool_contract, contract_owner):
    lending_pool_contract.deprecate({"from": contract_owner})

    with brownie.reverts("The pool is already deprecated"):
        lending_pool_contract.deprecate({"from": contract_owner})


def test_deposit_zero_investment(lending_pool_contract, investor):
    with brownie.reverts("Amount deposited has to be higher than 0"):
        lending_pool_contract.deposit(0, False, {"from": investor})


def test_amount_not_allowed(lending_pool_contract, erc20_contract, investor):
    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})


def test_insufficient_amount_allowed(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    
    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})


def test_deposit(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    funds_from_address = tx_deposit.return_value

    assert funds_from_address["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert funds_from_address["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert funds_from_address["totalAmountWithdrawn"] == 0
    assert funds_from_address["currentPendingRewards"] == 0
    assert funds_from_address["totalRewardsAmount"] == 0
    assert funds_from_address["activeForRewards"] == True
    assert funds_from_address["autoCompoundRewards"] == False
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")

    assert tx_deposit.events[-1]["_from"] == investor
    assert tx_deposit.events[-1]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events[-1]["erc20TokenContract"] == erc20_contract


def test_deposit_twice(lending_pool_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    tx_deposit_twice = lending_pool_contract.deposit(Web3.toWei(0.5, "ether"), False, {"from": investor})

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
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
    with brownie.reverts("The sender has less funds deposited than the amount requested"):
        lending_pool_contract.withdraw(Web3.toWei(1.5, "ether"), {"from": investor})


def test_withdraw(lending_pool_contract, erc20_contract, investor, contract_owner):
    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(2, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
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

    assert tx_withdraw.events[-1]["_from"] == investor
    assert tx_withdraw.events[-1]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events[-1]["erc20TokenContract"] == erc20_contract


def test_send_funds_wrong_sender(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    with brownie.reverts("Only the loans contract address can request to send funds"):
        lending_pool_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": investor})


def test_send_funds_zero_amount(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    with brownie.reverts("The amount to send should be higher than 0"):
        lending_pool_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": contract_owner}
        )


def test_send_funds_wrong_amount(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
    tx_send = lending_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_contract.fundsInvested() == Web3.toWei(0.2, "ether")

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
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_contract.fundsInvested() == 0
    assert lending_pool_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")
    
    assert lending_pool_contract.totalRewards() == Web3.toWei(expectedPoolFees, "ether")

    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == Web3.toWei(expectedPoolFees, "ether")
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(expectedPoolFees, "ether")

    assert tx_receive.events[-1]["_from"] == contract_owner
    assert tx_receive.events[-1]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events[-1]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events[-1]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_send.events[-1]["erc20TokenContract"] == erc20_contract


def test_receive_funds_multiple_lenders(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    erc20_contract.mint(contract_owner, Web3.toWei(3, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(3, "ether"), {"from": contract_owner})
    lending_pool_contract.deposit(Web3.toWei(3, "ether"), False, {"from": contract_owner})

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

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_contract.fundsAvailable() == Web3.toWei(4, "ether")
    assert lending_pool_contract.fundsInvested() == 0
    assert lending_pool_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")
    
    assert lending_pool_contract.totalRewards() == Web3.toWei(expectedPoolFees, "ether")

    expectedLenderOneRewards = expectedPoolFees * Decimal(1) / Decimal(4)
    expectedLenderTwoRewards = expectedPoolFees * Decimal(3) / Decimal(4)

    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == Web3.toWei(expectedLenderOneRewards, "ether")
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(expectedLenderOneRewards, "ether")
    assert lending_pool_contract.funds(contract_owner)["currentPendingRewards"] == Web3.toWei(expectedLenderTwoRewards, "ether")
    assert lending_pool_contract.funds(contract_owner)["totalRewardsAmount"] == Web3.toWei(expectedLenderTwoRewards, "ether")

    assert tx_receive.events[-1]["_from"] == contract_owner
    assert tx_receive.events[-1]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events[-1]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events[-1]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_send.events[-1]["erc20TokenContract"] == erc20_contract


def test_compound_rewards_no_deposits(lending_pool_contract, investor):
    with brownie.reverts("The sender has no funds deposited"):
        lending_pool_contract.compoundRewards({"from": investor})


def test_compound_rewards_no_pending_rewards(lending_pool_contract, erc20_contract, contract_owner, investor):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
    with brownie.reverts("The sender has no pending rewards to compound"):
        lending_pool_contract.compoundRewards({"from": investor})    


def test_compound_rewards(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    tx_compound = lending_pool_contract.compoundRewards({"from": investor})

    assert lending_pool_contract.funds(investor)["currentAmountDeposited"] == Web3.toWei(1 + expectedPoolFees, "ether")
    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == 0
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(expectedPoolFees, "ether")
    assert lending_pool_contract.funds(investor)["activeForRewards"] == True

    assert tx_compound.events[-1]["_from"] == investor
    assert tx_compound.events[-1]["rewards"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_compound.events[-1]["erc20TokenContract"] == erc20_contract


def test_rewards_computation(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

    expectedPoolFees = Decimal(0.02) * Decimal(10000 - PROTOCOL_FEES_SHARE) / Decimal(10000)

    init_of_day = int(dt.today().timestamp()) - int(dt.today().timestamp()) % 86400
    assert lending_pool_contract.days(0) == init_of_day
    assert lending_pool_contract.rewardsByDay(init_of_day) == Web3.toWei(expectedPoolFees, "ether")


def test_rewards_computation_over_two_days(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

    expectedPoolFeesDay1 = Decimal(0.02) * Decimal(10000 - PROTOCOL_FEES_SHARE) / Decimal(10000)

    init_of_day_one = int(dt.today().timestamp()) - int(dt.today().timestamp()) % 86400
    assert lending_pool_contract.days(0) == init_of_day_one
    assert lending_pool_contract.rewardsByDay(init_of_day_one) == Web3.toWei(expectedPoolFeesDay1, "ether")

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

    expectedPoolFeesDay2 = 0.03 * (10000 - PROTOCOL_FEES_SHARE) / 10000

    init_of_day_two = init_of_day_one + 86400
    
    assert lending_pool_contract.days(0) == init_of_day_one
    assert lending_pool_contract.days(1) == init_of_day_two
    assert lending_pool_contract.rewardsByDay(init_of_day_one) == Web3.toWei(expectedPoolFeesDay1, "ether")
    assert lending_pool_contract.rewardsByDay(init_of_day_two) == Web3.toWei(expectedPoolFeesDay2, "ether")


def test_rewards_computation_over_several_days(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})
    
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

        expectedPoolFees = 0.02 * (10000 - PROTOCOL_FEES_SHARE) / 10000

        if day in [7, 8]:
            init_of_day = initial_day_timestamp + 86400 * day
            assert lending_pool_contract.days(day - 7) == init_of_day
            assert lending_pool_contract.rewardsByDay(init_of_day) == Web3.toWei(expectedPoolFees, "ether")
            assert lending_pool_contract.lastDaysApr(7) / 10**18 == expectedPoolFees * 7 * 365 / 7


def test_change_autocompound_setting_same_setting(lending_pool_contract):
   with brownie.reverts("The sender is not participating in the pool"):
        lending_pool_contract.changeAutoCompoundRewardsSetting(False, {"from": investor})


def test_change_autocompound_setting_same_setting(lending_pool_contract, erc20_contract, contract_owner, investor):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    with brownie.reverts("The value passed should be different than the current setting"):
        lending_pool_contract.changeAutoCompoundRewardsSetting(False, {"from": investor})


def test_change_autocompound_setting(lending_pool_contract, erc20_contract, contract_owner, investor):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    tx = lending_pool_contract.changeAutoCompoundRewardsSetting(True, {"from": investor})

    assert tx.return_value["autoCompoundRewards"] == True


def test_autocompounding(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), True, {"from": investor})
    
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

    expectedPoolFees = Decimal(0.02) * Decimal(10000 - PROTOCOL_FEES_SHARE) / Decimal(10000)
    
    assert lending_pool_contract.funds(investor)["currentAmountDeposited"] == Web3.toWei(1 + expectedPoolFees, "ether")
    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == 0
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(expectedPoolFees, "ether")


def test_autocompounding_multiple_lenders(lending_pool_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(1, "ether"), True, {"from": investor})

    erc20_contract.mint(contract_owner, Web3.toWei(3, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(3, "ether"), {"from": contract_owner})
    tx_deposit = lending_pool_contract.deposit(Web3.toWei(3, "ether"), False, {"from": contract_owner})
    
    tx_send = lending_pool_contract.sendFunds(
        borrower,
        Web3.toWei(0.4, "ether"),
        {"from": contract_owner}
    )

    erc20_contract.mint(borrower, Web3.toWei(0.44, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(0.44, "ether"), {"from": borrower})

    tx_receive = lending_pool_contract.receiveFunds(
        borrower,
        Web3.toWei(0.4, "ether"),
        Web3.toWei(0.04, "ether"),
        {"from": contract_owner}
    )

    expectedPoolFees = Decimal(0.04) * Decimal(10000 - PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedLenderOneRewards = expectedPoolFees * Decimal(1) / Decimal(4)
    expectedLenderTwoRewards = expectedPoolFees * Decimal(3) / Decimal(4)
    
    assert lending_pool_contract.funds(investor)["currentAmountDeposited"] == Web3.toWei(1 + expectedLenderOneRewards, "ether")
    assert lending_pool_contract.funds(investor)["currentPendingRewards"] == 0
    assert lending_pool_contract.funds(investor)["totalRewardsAmount"] == Web3.toWei(expectedLenderOneRewards, "ether")

    assert lending_pool_contract.funds(contract_owner)["currentAmountDeposited"] == Web3.toWei(3, "ether")
    assert lending_pool_contract.funds(contract_owner)["currentPendingRewards"] == Web3.toWei(expectedLenderTwoRewards, "ether")
    assert lending_pool_contract.funds(contract_owner)["totalRewardsAmount"] == Web3.toWei(expectedLenderTwoRewards, "ether")
