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


def test_initial_state(lending_pool_peripheral_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_peripheral_contract.owner() == contract_owner
    assert lending_pool_peripheral_contract.erc20TokenContract() == erc20_contract
    assert lending_pool_peripheral_contract.protocolWallet() == protocol_wallet
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY
    assert lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolDeprecated()
    assert not lending_pool_peripheral_contract.isPoolInvesting()
    assert not lending_pool_peripheral_contract.whitelistEnabled()


def test_change_ownership_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("Only the owner can change the contract ownership"):
        lending_pool_peripheral_contract.changeOwnership(borrower, {"from": borrower})


def test_change_ownership(lending_pool_peripheral_contract, borrower, contract_owner):
    lending_pool_peripheral_contract.changeOwnership(borrower, {"from": contract_owner})
    assert lending_pool_peripheral_contract.owner() == borrower

    lending_pool_peripheral_contract.changeOwnership(contract_owner, {"from": borrower})
    assert lending_pool_peripheral_contract.owner() == contract_owner


def test_change_max_capital_efficiency_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("Only the owner can change the max capital efficiency"):
        lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY + 1000, {"from": borrower})


def test_change_max_capital_efficiency(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY + 1000, {"from": contract_owner})
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY + 1000

    lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY, {"from": contract_owner})
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY


def test_change_protocol_wallet_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("Only the owner can change the protocol wallet address"):
        lending_pool_peripheral_contract.changeProtocolWallet(borrower, {"from": borrower})


def test_change_protocol_wallet(lending_pool_peripheral_contract, contract_owner, protocol_wallet):
    lending_pool_peripheral_contract.changeProtocolWallet(contract_owner, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolWallet() == contract_owner

    lending_pool_peripheral_contract.changeProtocolWallet(protocol_wallet, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolWallet() == protocol_wallet


def test_change_protocol_fees_share_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("Only the owner can change the protocol fees share"):
        lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE + 1000, {"from": borrower})


def test_change_protocol_fees_share(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE + 1000, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE + 1000

    lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE


def test_change_pool_status_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("Only the owner can change the pool status"):
        lending_pool_peripheral_contract.changePoolStatus(False, {"from": borrower})


def test_change_pool_status_same_status(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("The new pool status should be different than the current status"):
        lending_pool_peripheral_contract.changePoolStatus(True, {"from": contract_owner})


def test_change_pool_status(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    assert lending_pool_peripheral_contract.isPoolActive() == False
    assert lending_pool_peripheral_contract.isPoolInvesting() == False
    assert tx.return_value == lending_pool_peripheral_contract.isPoolActive()


def test_change_pool_status_again(lending_pool_peripheral_contract, lending_pool_core_contract, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    tx = lending_pool_peripheral_contract.changePoolStatus(True, {"from": contract_owner})

    assert lending_pool_peripheral_contract.isPoolActive() == True
    assert lending_pool_peripheral_contract.isPoolInvesting() == False
    assert tx.return_value == lending_pool_peripheral_contract.isPoolActive()


def test_deprecate_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("Only the owner can change the pool to deprecated"):
        lending_pool_peripheral_contract.deprecate({"from": borrower})


def test_deprecate(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    assert lending_pool_peripheral_contract.isPoolDeprecated() == True
    assert lending_pool_peripheral_contract.isPoolActive() == False
    assert lending_pool_peripheral_contract.isPoolInvesting() == False
    assert tx.return_value == lending_pool_peripheral_contract.isPoolDeprecated()


def test_deprecate_already_deprecated(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("The pool is already deprecated"):
        lending_pool_peripheral_contract.deprecate({"from": contract_owner})


def test_change_whitelist_status_wrong_sender(lending_pool_peripheral_contract, investor):
    with brownie.reverts("Only the owner can change the whitelist status"):
        lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": investor})


def test_change_whitelist_status_same_status(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("The new whitelist status should be different than the current status"):
        lending_pool_peripheral_contract.changeWhitelistStatus(False, {"from": contract_owner})


def test_change_whitelist_status(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.changeWhitelistStatus(False, {"from": contract_owner})
    assert not lending_pool_peripheral_contract.whitelistEnabled()


def test_add_whitelisted_address_wrong_sender(lending_pool_peripheral_contract, investor):
    with brownie.reverts("Only the owner can add addresses to the whitelist"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": investor})


def test_add_whitelisted_address_whitelist_disabled(lending_pool_peripheral_contract, contract_owner, investor):
    with brownie.reverts("The whitelist is disabled"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})


def test_add_whitelisted_address(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)


def test_add_whitelisted_address_already_whitelisted(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    with brownie.reverts("The address is already whitelisted"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})


def test_remove_whitelisted_address_wrong_sender(lending_pool_peripheral_contract, investor):
    with brownie.reverts("Only the owner can remove addresses from the whitelist"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": investor})


def test_remove_whitelisted_address_whitelist_disabled(lending_pool_peripheral_contract, contract_owner, investor):
    with brownie.reverts("The whitelist is disabled"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": contract_owner})


def test_remove_whitelisted_address_not_whitelisted(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    with brownie.reverts("The address is not whitelisted"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": contract_owner})


def test_remove_whitelisted_address(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": contract_owner})
    assert not lending_pool_peripheral_contract.whitelistedAddresses(investor)  


def test_deposit_deprecated(lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("Pool is deprecated, please withdraw any outstanding deposit"):
        lending_pool_peripheral_contract.deposit(0, {"from": investor})


def test_deposit_inactive(lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    with brownie.reverts("Pool is not active right now"):
        lending_pool_peripheral_contract.deposit(0, {"from": investor})


def test_deposit_zero_investment(lending_pool_peripheral_contract, investor):
    with brownie.reverts("Amount deposited has to be higher than 0"):
        lending_pool_peripheral_contract.deposit(0, {"from": investor})


def test_deposit_insufficient_amount_allowed(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    
    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})


def test_deposit_not_whitelisted(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})
    
    with brownie.reverts("The whitelist is enabled and the sender is not whitelisted"):
        lending_pool_peripheral_contract.deposit(deposit_amount, {"from": investor})


def test_deposit_whitelisted(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    tx_deposit = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == True
    
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert tx_deposit.events["Deposit"]["wallet"] == investor
    assert tx_deposit.events["Deposit"]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events["Deposit"]["erc20TokenContract"] == erc20_contract


def test_deposit(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    tx_deposit = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == True
    
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert tx_deposit.events["Deposit"]["wallet"] == investor
    assert tx_deposit.events["Deposit"]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events["Deposit"]["erc20TokenContract"] == erc20_contract


def test_deposit_twice(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.5, "ether"), {"from": investor})
    tx_deposit_twice = lending_pool_peripheral_contract.deposit(Web3.toWei(0.5, "ether"), {"from": investor})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1.5, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1.5, "ether")

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1.5, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert tx_deposit.events["Deposit"]["wallet"] == investor
    assert tx_deposit.events["Deposit"]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events["Deposit"]["erc20TokenContract"] == erc20_contract

    assert tx_deposit_twice.events["Deposit"]["wallet"] == investor
    assert tx_deposit_twice.events["Deposit"]["amount"] == Web3.toWei(0.5, "ether")
    assert tx_deposit_twice.events["Deposit"]["erc20TokenContract"] == erc20_contract


def test_withdraw_zero_amount(lending_pool_peripheral_contract, investor):
    with brownie.reverts("Amount withdrawn has to be higher than 0"):
        lending_pool_peripheral_contract.withdraw(0, {"from": investor})


def test_withdraw_noinvestment(lending_pool_peripheral_contract, lending_pool_core_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    
    with brownie.reverts("The sender has insufficient liquidity for withdrawal"):
        lending_pool_peripheral_contract.withdraw(Web3.toWei(1, "ether"), {"from": investor})


def test_withdraw_insufficient_investment(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_deposit = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("The sender has insufficient liquidity for withdrawal"):
        lending_pool_peripheral_contract.withdraw(Web3.toWei(1.5, "ether"), {"from": investor})


def test_withdraw(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, investor, contract_owner):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    initial_balance = user_balance(erc20_contract, investor)
    
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(2, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")

    tx_deposit = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    tx_withdraw = lending_pool_peripheral_contract.withdraw(Web3.toWei(1, "ether"), {"from": investor})
    assert user_balance(erc20_contract, investor) == initial_balance + Web3.toWei(2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == 0

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["currentAmountDeposited"] == 0
    assert investor_funds["totalAmountWithdrawn"] == Web3.toWei(1, "ether")
    assert investor_funds["sharesBasisPoints"] == 0
    assert investor_funds["activeForRewards"] == False

    assert tx_withdraw.events["Withdrawal"]["wallet"] == investor
    assert tx_withdraw.events["Withdrawal"]["amount"] == Web3.toWei(1, "ether")
    assert tx_withdraw.events["Withdrawal"]["erc20TokenContract"] == erc20_contract


def test_send_funds_deprecated(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("Pool is deprecated"):
        lending_pool_peripheral_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": contract_owner})


def test_send_funds_inactive(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    with brownie.reverts("The pool is not active and is not investing more right now"):
        lending_pool_peripheral_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": contract_owner})


def test_send_funds_wrong_sender(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    with brownie.reverts("Only the loans contract address can request to send funds"):
        lending_pool_peripheral_contract.sendFunds(borrower, Web3.toWei(1, "ether"), {"from": investor})


def test_send_funds_zero_amount(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    with brownie.reverts("The amount to send should be higher than 0"):
        lending_pool_peripheral_contract.sendFunds(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": contract_owner}
        )


def test_send_funds_wrong_amount(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    with brownie.reverts("No sufficient deposited funds to perform the transaction"):
        lending_pool_peripheral_contract.sendFunds(
            borrower,
            Web3.toWei(2, "ether"),
            {"from": contract_owner}
        )


def test_send_funds_insufficient_funds_to_lend(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    with brownie.reverts("No sufficient deposited funds to perform the transaction"):
        tx_send = lending_pool_peripheral_contract.sendFunds(
            borrower,
            Web3.toWei(0.8, "ether"),
            {"from": contract_owner}
        )


def test_send_funds(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    initial_balance = user_balance(erc20_contract, borrower)
    
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    tx_send = lending_pool_peripheral_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.toWei(0.2, "ether")

    assert tx_send.events["FundsTransfer"]["wallet"] == borrower
    assert tx_send.events["FundsTransfer"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_send.events["FundsTransfer"]["erc20TokenContract"] == erc20_contract


# TODO: change


def test_receive_funds_wrong_sender(lending_pool_peripheral_contract, borrower, contract_owner):
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    with brownie.reverts("The sender address is not the loans contract address"):
        lending_pool_peripheral_contract.receiveFunds(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower}
        )


def test_receive_funds_insufficient_amount(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    with brownie.reverts("Insufficient funds allowed to be transfered"):
        lending_pool_peripheral_contract.receiveFunds(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": contract_owner}
        )


def test_receive_funds_zero_value(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    with brownie.reverts("The sent value should be higher than 0"):
        lending_pool_peripheral_contract.receiveFunds(
            borrower,
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": contract_owner}
        )


def test_receive_funds(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower, protocol_wallet):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    erc20_contract.mint(borrower, Web3.toWei(0.02, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.22, "ether"), {"from": borrower})

    tx_receive = lending_pool_peripheral_contract.receiveFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": contract_owner}
    )

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1 + expectedPoolFees, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0
    assert lending_pool_core_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")

    assert lending_pool_core_contract.totalRewards() == Web3.toWei(expectedPoolFees, "ether")

    assert lending_pool_core_contract.funds(investor)["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == Web3.toWei(1 + expectedPoolFees, "ether")

    assert user_balance(erc20_contract, protocol_wallet) == Web3.toWei(expectedProtocolFees, "ether")
    assert user_balance(erc20_contract, lending_pool_core_contract) == Web3.toWei(1 + expectedPoolFees, "ether")

    assert tx_receive.events["FundsReceipt"]["wallet"] == contract_owner
    assert tx_receive.events["FundsReceipt"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["erc20TokenContract"] == erc20_contract


def test_receive_funds_multiple_lenders(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, investor, borrower, protocol_wallet):
    lending_pool_peripheral_contract.setLendingPoolCoreAddress(lending_pool_core_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(contract_owner, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    erc20_contract.mint(contract_owner, Web3.toWei(3, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(3, "ether"), {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(Web3.toWei(3, "ether"), {"from": contract_owner})

    tx_send = lending_pool_peripheral_contract.sendFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": contract_owner}
    )

    erc20_contract.mint(borrower, Web3.toWei(0.22, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.22, "ether"), {"from": borrower})

    tx_receive = lending_pool_peripheral_contract.receiveFunds(
        borrower,
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": contract_owner}
    )

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(4 + expectedPoolFees, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0
    assert lending_pool_core_contract.totalFundsInvested() == Web3.toWei(0.2, "ether")
    
    assert lending_pool_core_contract.totalRewards() == Web3.toWei(expectedPoolFees, "ether")

    expectedLenderOneRewards = expectedPoolFees * Decimal(1) / Decimal(4)
    expectedLenderTwoRewards = expectedPoolFees * Decimal(3) / Decimal(4)

    assert lending_pool_core_contract.funds(investor)["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.funds(contract_owner)["sharesBasisPoints"] == Web3.toWei(3, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == Web3.toWei(1 + expectedLenderOneRewards, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(contract_owner) == Web3.toWei(3 + expectedLenderTwoRewards, "ether")

    assert user_balance(erc20_contract, protocol_wallet) == Web3.toWei(expectedProtocolFees, "ether")
    assert user_balance(erc20_contract, lending_pool_core_contract) == Web3.toWei(4 + expectedPoolFees, "ether")

    assert tx_receive.events["FundsReceipt"]["wallet"] == contract_owner
    assert tx_receive.events["FundsReceipt"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["erc20TokenContract"] == erc20_contract
