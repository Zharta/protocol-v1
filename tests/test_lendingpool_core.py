from multiprocessing import pool
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
def lending_pool_peripheral_contract(LendingPoolPeripheral, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolPeripheral.deploy(
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture
def lending_pool_core_contract(LendingPoolCore, lending_pool_peripheral_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolCore.deploy(
        lending_pool_peripheral_contract,
        erc20_contract,
        {'from': contract_owner}
    )


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)


def test_initial_state(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_core_contract.owner() == contract_owner
    assert lending_pool_core_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract
    assert lending_pool_core_contract.erc20TokenContract() == erc20_contract


def test_change_ownership_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("Only the owner can change the contract ownership"):
        lending_pool_core_contract.changeOwnership(borrower, {"from": borrower})


def test_change_ownership(lending_pool_core_contract, borrower, contract_owner):
    lending_pool_core_contract.changeOwnership(borrower, {"from": contract_owner})
    assert lending_pool_core_contract.owner() == borrower

    lending_pool_core_contract.changeOwnership(contract_owner, {"from": borrower})
    assert lending_pool_core_contract.owner() == contract_owner


def test_deposit_wrong_sender(lending_pool_core_contract, investor, borrower):
    with brownie.reverts("Only defined lending pool peripheral can deposit"):
        lending_pool_core_contract.deposit(investor, 0, {"from": borrower})


def test_deposit_zero_investment(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    with brownie.reverts("Amount deposited has to be higher than 0"):
        lending_pool_core_contract.deposit(investor, 0, {"from": lending_pool_peripheral_contract})


def test_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    tx_deposit = lending_pool_core_contract.deposit(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    assert tx_deposit.return_value

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == True
    
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]
    assert lending_pool_core_contract.totalSharesBasisPoints() == Web3.toWei(1, "ether")


def test_deposit_twice(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    tx_deposit = lending_pool_core_contract.deposit(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    tx_deposit_twice = lending_pool_core_contract.deposit(investor, Web3.toWei(0.5, "ether"), {"from": lending_pool_peripheral_contract})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1.5, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1.5, "ether")
    assert investor_funds["sharesBasisPoints"] == Web3.toWei(1.5, "ether")
    
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1.5, "ether")
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]
    assert lending_pool_core_contract.totalSharesBasisPoints() == Web3.toWei(1.5, "ether")


def test_transfer_deposit_wrong_sender(lending_pool_core_contract, investor):
    with brownie.reverts("Only defined lending pool peripheral can request a deposit transfer"):
        lending_pool_core_contract.transferDeposit(investor, 0, {"from": investor})


def test_transfer_deposit_lender_zeroaddress(lending_pool_core_contract, lending_pool_peripheral_contract):
    with brownie.reverts("The lender can not be the empty address"):
        lending_pool_core_contract.transferDeposit(brownie.ZERO_ADDRESS, 0, {"from": lending_pool_peripheral_contract})


def test_transfer_deposit_lender_zeroaddress(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    with brownie.reverts("Amount deposited has to be higher than 0"):
        lending_pool_core_contract.transferDeposit(investor, 0, {"from": lending_pool_peripheral_contract})


def test_transfer_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    deposit_amount = Web3.toWei(2, "ether")
    
    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + deposit_amount

    lending_pool_core_contract.transferDeposit(investor, deposit_amount, {"from": lending_pool_peripheral_contract})


def test_withdraw_wrong_sender(lending_pool_core_contract, lending_pool_peripheral_contract, investor, borrower):
    with brownie.reverts("Only defined lending pool peripheral can withdraw"):
        lending_pool_core_contract.withdraw(investor, 100, {"from": borrower})


def test_withdraw_zero_amount(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    with brownie.reverts("Amount withdrawn has to be higher than 0"):
        lending_pool_core_contract.withdraw(investor, 0, {"from": lending_pool_peripheral_contract})


def test_withdraw_lender_zeroaddress(lending_pool_core_contract, lending_pool_peripheral_contract):
    with brownie.reverts("The lender can not be the empty address"):
        lending_pool_core_contract.withdraw(brownie.ZERO_ADDRESS, 100, {"from": lending_pool_peripheral_contract})


def test_withdraw_noinvestment(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    with brownie.reverts("The lender has less funds deposited than the amount requested"):
        lending_pool_core_contract.withdraw(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})


def test_withdraw_insufficient_investment(lending_pool_core_contract, lending_pool_peripheral_contract, investor):
    lending_pool_core_contract.deposit(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    
    with brownie.reverts("The lender has less funds deposited than the amount requested"):
        lending_pool_core_contract.withdraw(investor, Web3.toWei(1.5, "ether"), {"from": lending_pool_peripheral_contract})


def test_withdraw(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    deposit_amount = Web3.toWei(2, "ether")
    withdraw_amount = Web3.toWei(1, "ether")

    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + deposit_amount

    tx_deposit = lending_pool_peripheral_contract.deposit(deposit_amount, {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount

    tx_withdraw = lending_pool_core_contract.withdraw(investor, withdraw_amount, {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance + withdraw_amount
    assert lending_pool_core_contract.fundsAvailable() == deposit_amount - withdraw_amount

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == deposit_amount - withdraw_amount
    assert investor_funds["totalAmountDeposited"] == deposit_amount
    assert investor_funds["totalAmountWithdrawn"] == withdraw_amount
    assert investor_funds["activeForRewards"]

    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]


def test_deposit_withdraw_deposit(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(2, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    tx_deposit = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    tx_withdraw = lending_pool_core_contract.withdraw(investor, Web3.toWei(1, "ether"), {"from": lending_pool_peripheral_contract})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == 0

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == 0
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == False

    assert lending_pool_core_contract.activeLenders() == 0
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]

    tx_deposit2 = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    investor_funds2 = lending_pool_core_contract.funds(investor)
    assert investor_funds2["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds2["totalAmountDeposited"] == Web3.toWei(2, "ether")
    assert investor_funds2["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert investor_funds2["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds2["activeForRewards"] == True
    
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.activeLenders() == 1
    assert lending_pool_core_contract.knownLenders(investor)
    assert lending_pool_core_contract.lendersArray() == [investor]
    assert lending_pool_core_contract.totalSharesBasisPoints() == Web3.toWei(1, "ether")


def test_send_funds_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("Only defined lending pool peripheral can send funds"):
        lending_pool_core_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": borrower})


def test_send_funds_zero_amount(lending_pool_core_contract, lending_pool_peripheral_contract, borrower):
    with brownie.reverts("The amount to send should be higher than 0"):
        lending_pool_core_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_send_funds_insufficient_balance(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("Insufficient balance"):
        tx_send = lending_pool_core_contract.sendFunds(
            borrower,
            Web3.toWei(1.1, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_send_funds(
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    initial_balance = user_balance(erc20_contract, borrower)
    
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    tx_send = lending_pool_core_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.toWei(0.2, "ether")


def test_receive_funds_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("Only defined lending pool peripheral can receive funds"):
        lending_pool_core_contract.receiveFunds(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower}
        )


def test_receive_funds_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, borrower):
    with brownie.reverts("The sent value should be higher than 0"):
        lending_pool_core_contract.receiveFunds(
            borrower,
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )

def test_transfer_protocol_fees_wrong_sender(lending_pool_core_contract, contract_owner, borrower):
    with brownie.reverts("Only defined lending pool peripheral can ask for protocol fees"):
        lending_pool_core_contract.transferProtocolFees(
            contract_owner,
            Web3.toWei(0.2, "ether"),
            {"from": borrower}
        )


def test_transfer_protocol_fees_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("The requested value should be higher than 0"):
        lending_pool_core_contract.transferProtocolFees(
            contract_owner,
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_transfer_protocol_fees(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):  
    erc20_contract.mint(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": contract_owner})

    assert user_balance(erc20_contract, lending_pool_core_contract) == Web3.toWei(1, "ether")

    lending_pool_core_contract.transferProtocolFees(
        contract_owner,
        Web3.toWei(1, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == 0
    assert user_balance(erc20_contract, contract_owner) == Web3.toWei(1, "ether")


def test_receive_funds(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, borrower, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(borrower, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": borrower})

    lending_amount = Web3.toWei(0.2, "ether")
    rewards_amount = Web3.toWei(0.02, "ether")
    pool_rewards_amount = rewards_amount * (10000 - lending_pool_peripheral_contract.protocolFeesShare()) / 10000

    initial_balance = user_balance(erc20_contract, lending_pool_core_contract)

    lending_pool_core_contract.receiveFunds(
        borrower,
        lending_amount,
        pool_rewards_amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert user_balance(erc20_contract, lending_pool_core_contract) == initial_balance + lending_amount + pool_rewards_amount


def test_update_liquidity_wrong_sender(lending_pool_core_contract, borrower):
    with brownie.reverts("Only defined lending pool peripheral can update liquidity data"):
        lending_pool_core_contract.updateLiquidity(
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower}
        )


def test_update_liquidity_zero_value(lending_pool_core_contract, lending_pool_peripheral_contract):
    with brownie.reverts("The sent value should be higher than 0"):
        lending_pool_core_contract.updateLiquidity(
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": lending_pool_peripheral_contract}
        )


def test_update_liquidity_too_much_funds(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, borrower, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    with brownie.reverts("There are more funds being received than expected by the deposited funds variable"):
        lending_pool_core_contract.updateLiquidity(
            Web3.toWei(0.3, "ether"),
            0,
            {"from": lending_pool_peripheral_contract}
        )


def test_update_liquidity(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, investor, borrower, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    lending_pool_peripheral_contract.deposit(deposit_amount, {"from": investor})

    lending_pool_core_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": lending_pool_peripheral_contract}
    )

    lending_amount = Web3.toWei(0.2, "ether")
    rewards_amount = Web3.toWei(0.02, "ether")
    pool_rewards_amount = rewards_amount * (10000 - lending_pool_peripheral_contract.protocolFeesShare()) / 10000

    lending_pool_core_contract.updateLiquidity(
        lending_amount,
        pool_rewards_amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert lending_pool_core_contract.fundsAvailable() == deposit_amount + pool_rewards_amount
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_core_contract.totalRewards() == pool_rewards_amount
    assert lending_pool_core_contract.totalSharesBasisPoints() == deposit_amount

    assert lending_pool_core_contract.funds(contract_owner)["sharesBasisPoints"] == 0
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == deposit_amount + pool_rewards_amount


def test_update_liquidity_multiple_lenders(lending_pool_core_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    lender_one_deposit_amount = Web3.toWei(1, "ether")
    lender_two_deposit_amount = Web3.toWei(3, "ether")

    erc20_contract.mint(investor, lender_one_deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, lender_one_deposit_amount, {"from": investor})
    lending_pool_peripheral_contract.deposit(lender_one_deposit_amount, {"from": investor})

    erc20_contract.mint(contract_owner, lender_two_deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, lender_two_deposit_amount, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(lender_two_deposit_amount, {"from": contract_owner})

    deposits_amount = lender_one_deposit_amount + lender_two_deposit_amount
    investment_amount = Web3.toWei(0.2, "ether")
    rewards_amount = Web3.toWei(0.02, "ether")

    lending_pool_core_contract.sendFunds(
        borrower,
        investment_amount,
        {"from": lending_pool_peripheral_contract}
    )

    lending_pool_core_contract.updateLiquidity(
        investment_amount,
        rewards_amount,
        {"from": lending_pool_peripheral_contract}
    )

    assert lending_pool_core_contract.fundsAvailable() == deposits_amount + rewards_amount
    assert lending_pool_core_contract.fundsInvested() == 0
    assert lending_pool_core_contract.totalFundsInvested() == investment_amount
    assert lending_pool_core_contract.totalRewards() == rewards_amount

    expectedLenderOneRewards = rewards_amount * Decimal(1) / Decimal(4)
    expectedLenderTwoRewards = rewards_amount * Decimal(3) / Decimal(4)
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == Web3.toWei(1, "ether") + expectedLenderOneRewards
    assert lending_pool_core_contract.computeWithdrawableAmount(contract_owner) == Web3.toWei(3, "ether") + expectedLenderTwoRewards
