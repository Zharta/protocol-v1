from brownie import chain
from decimal import Decimal
from web3 import Web3

import brownie
import pytest


PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000

MAX_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


def user_balance(token_contract, user):
    return token_contract.balanceOf(user)


def test_change_loans_peripheral_address(
    lending_pool_peripheral_contract,
    loans_peripheral_contract,
    loans_peripheral_contract_aux,
    contract_owner,
    protocol_wallet
):
    tx = lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract_aux, {"from": contract_owner})
    assert lending_pool_peripheral_contract.loansContract() == loans_peripheral_contract_aux

    event = tx.events["LoansPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_peripheral_contract_aux

    tx = lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    assert lending_pool_peripheral_contract.loansContract() == loans_peripheral_contract

    event = tx.events["LoansPeripheralAddressSet"]
    assert event["currentValue"] == loans_peripheral_contract_aux
    assert event["newValue"] == loans_peripheral_contract


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_peripheral_contract.owner() == contract_owner
    assert lending_pool_peripheral_contract.lendingPoolCoreContract() == lending_pool_core_contract
    assert lending_pool_peripheral_contract.erc20TokenContract() == erc20_contract
    assert lending_pool_peripheral_contract.protocolWallet() == protocol_wallet
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY
    assert lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolDeprecated()
    assert not lending_pool_peripheral_contract.isPoolInvesting()
    assert not lending_pool_peripheral_contract.whitelistEnabled()


def test_propose_owner_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("_address it the zero address"):
        lending_pool_peripheral_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        lending_pool_peripheral_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(lending_pool_peripheral_contract, contract_owner, borrower):
    tx = lending_pool_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    assert lending_pool_peripheral_contract.proposedOwner() == borrower
    assert lending_pool_peripheral_contract.owner() == contract_owner

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        lending_pool_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        lending_pool_peripheral_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = lending_pool_peripheral_contract.claimOwnership({"from": borrower})

    assert lending_pool_peripheral_contract.owner() == borrower
    assert lending_pool_peripheral_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_change_max_capital_efficiency_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY, {"from": borrower})

def test_change_max_capital_efficiency_excess_value(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("capital eff exceeds 10000 bps"):
        lending_pool_peripheral_contract.changeMaxCapitalEfficiency(10001, {"from": contract_owner})


def test_change_max_capital_efficiency(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY + 1000, {"from": contract_owner})
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY + 1000

    event = tx.events["MaxCapitalEfficiencyChanged"]
    assert event["currentValue"] == MAX_CAPITAL_EFFICIENCY
    assert event["newValue"] == MAX_CAPITAL_EFFICIENCY + 1000

    tx = lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY, {"from": contract_owner})
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY

    event = tx.events["MaxCapitalEfficiencyChanged"]
    assert event["currentValue"] == MAX_CAPITAL_EFFICIENCY + 1000
    assert event["newValue"] == MAX_CAPITAL_EFFICIENCY


def test_change_protocol_wallet_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeProtocolWallet(borrower, {"from": borrower})


def test_change_protocol_wallet_zero_address(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.changeProtocolWallet(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_change_protocol_wallet(lending_pool_peripheral_contract, contract_owner, protocol_wallet):
    tx = lending_pool_peripheral_contract.changeProtocolWallet(contract_owner, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolWallet() == contract_owner

    event = tx.events["ProtocolWalletChanged"]
    assert event["currentValue"] == protocol_wallet
    assert event["newValue"] == contract_owner

    tx = lending_pool_peripheral_contract.changeProtocolWallet(protocol_wallet, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolWallet() == protocol_wallet

    event = tx.events["ProtocolWalletChanged"]
    assert event["currentValue"] == contract_owner
    assert event["newValue"] == protocol_wallet


def test_change_protocol_fees_share_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE + 1000, {"from": borrower})


def test_change_protocol_fees_share_excess_value(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("fees share exceeds 10000 bps"):
        lending_pool_peripheral_contract.changeProtocolFeesShare(10001, {"from": contract_owner})


def test_change_protocol_fees_share(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE + 1000, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE + 1000

    event = tx.events["ProtocolFeesShareChanged"]
    assert event["currentValue"] == PROTOCOL_FEES_SHARE
    assert event["newValue"] == PROTOCOL_FEES_SHARE + 1000

    tx = lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE, {"from": contract_owner})
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE

    event = tx.events["ProtocolFeesShareChanged"]
    assert event["currentValue"] == PROTOCOL_FEES_SHARE + 1000
    assert event["newValue"] == PROTOCOL_FEES_SHARE


def test_change_loans_peripheral_address_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.setLoansPeripheralAddress(borrower, {"from": borrower})


def test_change_loans_peripheral_address_zero_address(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.setLoansPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_change_loans_peripheral_address_not_contract(lending_pool_peripheral_contract, borrower, contract_owner):
    with brownie.reverts("_address is not a contract"):
        lending_pool_peripheral_contract.setLoansPeripheralAddress(borrower, {"from": contract_owner})


def test_change_whitelist_status_wrong_sender(lending_pool_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": investor})


def test_change_whitelist_status_same_status(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        lending_pool_peripheral_contract.changeWhitelistStatus(False, {"from": contract_owner})


def test_change_whitelist_status(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    event = tx.events["WhitelistStatusChanged"]
    assert event["value"]

    tx = lending_pool_peripheral_contract.changeWhitelistStatus(False, {"from": contract_owner})
    assert not lending_pool_peripheral_contract.whitelistEnabled()

    event = tx.events["WhitelistStatusChanged"]
    assert not event["value"]


def test_add_whitelisted_address_wrong_sender(lending_pool_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": investor})


def test_add_whitelisted_address_zero_address(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.addWhitelistedAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_whitelisted_address_whitelist_disabled(lending_pool_peripheral_contract, contract_owner, investor):
    with brownie.reverts("whitelist is disabled"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})


def test_add_whitelisted_address(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    tx = lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    event = tx.events["WhitelistAddressAdded"]
    assert event["value"] == investor


def test_add_whitelisted_address_already_whitelisted(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    with brownie.reverts("address is already whitelisted"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})


def test_remove_whitelisted_address_wrong_sender(lending_pool_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": investor})


def test_remove_whitelisted_address_zero_address(lending_pool_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_whitelisted_address_whitelist_disabled(lending_pool_peripheral_contract, contract_owner, investor):
    with brownie.reverts("whitelist is disabled"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": contract_owner})


def test_remove_whitelisted_address_not_whitelisted(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    with brownie.reverts("address is not whitelisted"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": contract_owner})


def test_remove_whitelisted_address(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    tx = lending_pool_peripheral_contract.removeWhitelistedAddress(investor, {"from": contract_owner})
    assert not lending_pool_peripheral_contract.whitelistedAddresses(investor)  

    event = tx.events["WhitelistAddressRemoved"]
    assert event["value"] == investor


def test_change_pool_status_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changePoolStatus(False, {"from": borrower})


def test_change_pool_status(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    assert not lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolInvesting()

    assert not tx.events["ContractStatusChanged"]["value"]
    assert not tx.events["InvestingStatusChanged"]["value"]


def test_change_pool_status_again(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    event = tx.events["ContractStatusChanged"]
    assert not event["value"]

    tx = lending_pool_peripheral_contract.changePoolStatus(True, {"from": contract_owner})

    assert lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolInvesting()

    assert tx.events["ContractStatusChanged"]["value"]


def test_deprecate_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.deprecate({"from": borrower})


def test_deprecate(lending_pool_peripheral_contract, contract_owner):
    tx = lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    assert lending_pool_peripheral_contract.isPoolDeprecated()
    assert not lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolInvesting()

    assert not tx.events["ContractStatusChanged"]["value"]
    assert not tx.events["InvestingStatusChanged"]["value"]
    assert tx.events["ContractDeprecated"] is not None


def test_deprecate_already_deprecated(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("pool is already deprecated"):
        lending_pool_peripheral_contract.deprecate({"from": contract_owner})


def test_default_fn_wrong_sender(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the WETH addr"):
        borrower.transfer(lending_pool_peripheral_contract, 1)


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_deprecated(lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("pool is deprecated, withdraw"):
        lending_pool_peripheral_contract.depositEth({"from": investor, 'value': 0})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_inactive(lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    with brownie.reverts("pool is not active right now"):
        lending_pool_peripheral_contract.depositEth({"from": investor, 'value': 0})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_zero_investment(lending_pool_peripheral_contract, investor):
    with brownie.reverts("_amount has to be higher than 0"):
        lending_pool_peripheral_contract.depositEth({"from": investor, 'value': 0})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_pool_share_surpassed(lending_pool_peripheral_contract, liquidity_controls_contract, investor, contract_owner):
    liquidity_controls_contract.changeMaxPoolShareConditions(True, MAX_POOL_SHARE, {"from": contract_owner})
    with brownie.reverts("max pool share surpassed"):
        lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})


def test_deposit_insufficient_amount_allowed(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    investor,
    contract_owner
):
    erc20_contract.mint(investor, Web3.toWei(0.5, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.5, "ether"), {"from": investor})

    with brownie.reverts("not enough funds allowed"):
        lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_not_whitelisted(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    investor,
    contract_owner
):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, {"from": investor})

    with brownie.reverts("msg.sender is not whitelisted"):
        lending_pool_peripheral_contract.depositEth({"from": investor, 'value': deposit_amount})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_whitelisted(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    investor,
    contract_owner
):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, {"from": contract_owner})
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))

    tx_deposit = lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == True

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    # First event is the deposit of the ETH in the WETH contract
    assert tx_deposit.events["Deposit"][1]["wallet"] == investor
    assert tx_deposit.events["Deposit"][1]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events["Deposit"][1]["erc20TokenContract"] == erc20_contract


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_eth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount = Web3.toWei(1, "ether")
    contract_owner.transfer(to=investor, amount=amount)
    tx_deposit = lending_pool_peripheral_contract.depositEth({"from": investor, "value": amount})

    chain_time = chain.time()

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == amount
    assert investor_funds["totalAmountDeposited"] == amount
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == amount
    assert investor_funds["activeForRewards"] == True

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period["lockPeriodEnd"] <= chain_time + LOCK_PERIOD_DURATION + 10  # 10s of buffer
    assert lock_period["lockPeriodAmount"] == amount

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    # First event is the deposit of the ETH in the WETH contract
    assert tx_deposit.events["Deposit"][1]["wallet"] == investor
    assert tx_deposit.events["Deposit"][1]["amount"] == amount
    assert tx_deposit.events["Deposit"][1]["erc20TokenContract"] == erc20_contract


def test_deposit_weth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount = Web3.toWei(1, "ether")
    erc20_contract.mint(investor, amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount, {"from": investor})

    tx_deposit = lending_pool_peripheral_contract.depositWeth(amount, {"from": investor})

    chain_time = chain.time()

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == amount
    assert investor_funds["totalAmountDeposited"] == amount
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == amount
    assert investor_funds["activeForRewards"] == True

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period["lockPeriodEnd"] <= chain_time + LOCK_PERIOD_DURATION + 10  # 10s of buffer
    assert lock_period["lockPeriodAmount"] == amount

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert tx_deposit.events["Deposit"]["wallet"] == investor
    assert tx_deposit.events["Deposit"]["amount"] == amount
    assert tx_deposit.events["Deposit"]["erc20TokenContract"] == erc20_contract


@pytest.mark.require_network("ganache-mainnet-fork")
def test_deposit_twice(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount1 = Web3.toWei(1, "ether")
    contract_owner.transfer(to=investor, amount=amount1)
    tx_deposit = lending_pool_peripheral_contract.depositEth({"from": investor, 'value': amount1})

    chain_time = chain.time()

    chain.mine(blocks=1, timedelta=LOCK_PERIOD_DURATION / 2)

    amount2 = Web3.toWei(0.5, "ether")
    contract_owner.transfer(to=investor, amount=amount2)
    tx_deposit_twice = lending_pool_peripheral_contract.depositEth({"from": investor, 'value': amount2})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == amount1 + amount2
    assert investor_funds["totalAmountDeposited"] == amount1 + amount2

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period["lockPeriodEnd"] <= chain_time + LOCK_PERIOD_DURATION + 10  # 10s of buffer
    assert lock_period["lockPeriodAmount"] == amount1 + amount2

    assert lending_pool_core_contract.fundsAvailable() == amount1 + amount2
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    # First event is the deposit of the ETH in the WETH contract
    assert tx_deposit.events["Deposit"][1]["wallet"] == investor
    assert tx_deposit.events["Deposit"][1]["amount"] == amount1
    assert tx_deposit.events["Deposit"][1]["erc20TokenContract"] == erc20_contract

    # First event is the deposit of the ETH in the WETH contract
    assert tx_deposit_twice.events["Deposit"][1]["wallet"] == investor
    assert tx_deposit_twice.events["Deposit"][1]["amount"] == amount2
    assert tx_deposit_twice.events["Deposit"][1]["erc20TokenContract"] == erc20_contract


def test_deposit_max_pool_share_enabled(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    erc20_contract.mint(contract_owner, Web3.toWei(3, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(3, "ether"), {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.depositWeth(Web3.toWei(3, "ether"), {"from": contract_owner})

    liquidity_controls_contract.changeMaxPoolShareConditions(True, 4000, {"from": contract_owner})

    tx_deposit = lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds["currentAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountDeposited"] == Web3.toWei(1, "ether")
    assert investor_funds["totalAmountWithdrawn"] == 0
    assert investor_funds["sharesBasisPoints"] == Web3.toWei(1, "ether")
    assert investor_funds["activeForRewards"] == True

    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(4, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert tx_deposit.events["Deposit"]["wallet"] == investor
    assert tx_deposit.events["Deposit"]["amount"] == Web3.toWei(1, "ether")
    assert tx_deposit.events["Deposit"]["erc20TokenContract"] == erc20_contract


def test_withdraw_zero_amount(lending_pool_peripheral_contract, investor):
    with brownie.reverts("_amount has to be higher than 0"):
        lending_pool_peripheral_contract.withdrawEth(0, {"from": investor})


def test_withdraw_noinvestment(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, investor, contract_owner):
    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_peripheral_contract.withdrawEth(Web3.toWei(1, "ether"), {"from": investor})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_withdraw_insufficient_investment(
    lending_pool_peripheral_contract,
    investor,
    contract_owner
):
    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_peripheral_contract.withdrawEth(Web3.toWei(1.5, "ether"), {"from": investor})

    with brownie.reverts("_amount more than withdrawable"):
        lending_pool_peripheral_contract.withdrawWeth(Web3.toWei(1.5, "ether"), {"from": investor})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_withdraw(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, investor, contract_owner):
    initial_balance = investor.balance()

    contract_owner.transfer(to=investor, amount=Web3.toWei(2, "ether"))
    assert investor.balance() == initial_balance + Web3.toWei(2, "ether")

    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})
    assert investor.balance() == initial_balance + Web3.toWei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(1, "ether")

    tx_withdraw = lending_pool_peripheral_contract.withdrawEth(Web3.toWei(1, "ether"), {"from": investor})
    assert investor.balance() == initial_balance + Web3.toWei(2, "ether")
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


@pytest.mark.require_network("ganache-mainnet-fork")
def test_withdraw_within_lock_period(
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    investor,
    contract_owner
):
    contract_owner.transfer(to=investor, amount=Web3.toWei(2, "ether"))
    liquidity_controls_contract.changeLockPeriodConditions(True, LOCK_PERIOD_DURATION*2, {"from": contract_owner})
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    with brownie.reverts("withdraw within lock period"):
        lending_pool_peripheral_contract.withdrawEth(Web3.toWei(1, "ether"), {"from": investor})

    with brownie.reverts("withdraw within lock period"):
        lending_pool_peripheral_contract.withdrawWeth(Web3.toWei(1, "ether"), {"from": investor})


def test_withdraw_within_lock_period_within_amount(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount1 = Web3.toWei(1, "ether")
    amount2 = Web3.toWei(2, "ether")
    erc20_contract.mint(investor, amount1 + amount2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount1 + amount2, {"from": investor})

    liquidity_controls_contract.changeLockPeriodConditions(True, LOCK_PERIOD_DURATION, {"from": contract_owner})
    lending_pool_peripheral_contract.depositWeth(amount1, {"from": investor})

    chain.mine(blocks=1, timedelta=LOCK_PERIOD_DURATION * 2)
    lending_pool_peripheral_contract.depositWeth(amount2, {"from": investor})
    lending_pool_peripheral_contract.withdrawWeth(amount1, {"from": investor})

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period["lockPeriodAmount"] == amount2


def test_withdraw_out_of_lock_period(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    erc20_contract.mint(investor, Web3.toWei(2, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(2, "ether"), {"from": investor})

    liquidity_controls_contract.changeLockPeriodConditions(True, LOCK_PERIOD_DURATION*2, {"from": contract_owner})

    lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    chain.mine(blocks=1, timedelta=LOCK_PERIOD_DURATION * 2)

    lending_pool_peripheral_contract.withdrawWeth(Web3.toWei(1, "ether"), {"from": investor})


def test_lock_period_migration(
    lending_pool_legacy_core_contract,
    lending_pool_lock_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    investor,
    contract_owner
):
    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(contract_owner, deposit_amount, {"from": contract_owner})
    erc20_contract.transfer(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_legacy_core_contract, deposit_amount, {"from": investor})

    lending_pool_legacy_core_contract.deposit(investor, deposit_amount, LOCK_PERIOD_DURATION, {"from": lending_pool_peripheral_contract})
    lending_pool_lock_contract.migrate(lending_pool_legacy_core_contract, [investor])

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period["lockPeriodAmount"] == deposit_amount
    assert lock_period["lockPeriodEnd"] == lending_pool_legacy_core_contract.funds(investor)["lockPeriodEnd"]


def test_lock_period_migration_twice(
    lending_pool_legacy_core_contract,
    lending_pool_lock_contract,
    lending_pool_peripheral_contract,
    erc20_contract,
    investor,
    contract_owner
):
    deposit_amount = Web3.toWei(1, "ether")

    erc20_contract.mint(contract_owner, deposit_amount, {"from": contract_owner})
    erc20_contract.transfer(investor, deposit_amount, {"from": contract_owner})
    erc20_contract.approve(lending_pool_legacy_core_contract, deposit_amount, {"from": investor})

    lending_pool_legacy_core_contract.deposit(investor, deposit_amount, 0, {"from": lending_pool_peripheral_contract})
    lending_pool_lock_contract.migrate(lending_pool_legacy_core_contract, [])

    with brownie.reverts("migration already done"):
        lending_pool_lock_contract.migrate(lending_pool_legacy_core_contract, [investor])


def test_send_funds_deprecated(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("pool is deprecated"):
        lending_pool_peripheral_contract.sendFundsWeth(borrower, Web3.toWei(1, "ether"), {"from": contract_owner})


def test_send_funds_inactive(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.changePoolStatus(False, {"from": contract_owner})

    with brownie.reverts("pool is inactive"):
        lending_pool_peripheral_contract.sendFundsWeth(borrower, Web3.toWei(1, "ether"), {"from": contract_owner})


def test_send_funds_wrong_sender(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, contract_owner, investor, borrower):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    with brownie.reverts("msg.sender is not the loans addr"):
        lending_pool_peripheral_contract.sendFundsWeth(borrower, Web3.toWei(1, "ether"), {"from": investor})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_send_funds_zero_amount(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    loans_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    with brownie.reverts("_amount has to be higher than 0"):
        lending_pool_peripheral_contract.sendFundsEth(
            borrower,
            Web3.toWei(0, "ether"),
            {"from": loans_peripheral_contract}
        )


@pytest.mark.require_network("ganache-mainnet-fork")
def test_send_funds_wrong_amount(
    lending_pool_peripheral_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    with brownie.reverts("insufficient liquidity"):
        lending_pool_peripheral_contract.sendFundsEth(
            borrower,
            Web3.toWei(2, "ether"),
            {"from": loans_peripheral_contract}
        )


@pytest.mark.require_network("ganache-mainnet-fork")
def test_send_funds_insufficient_funds_to_lend(
    lending_pool_peripheral_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    with brownie.reverts("insufficient liquidity"):
        tx_send = lending_pool_peripheral_contract.sendFundsEth(
            borrower,
            Web3.toWei(0.8, "ether"),
            {"from": loans_peripheral_contract}
        )


@pytest.mark.require_network("ganache-mainnet-fork")
def test_send_funds_eth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    initial_balance = borrower.balance()

    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))

    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    tx_send = lending_pool_peripheral_contract.sendFundsEth(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": loans_peripheral_contract}
    )

    assert borrower.balance() == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.toWei(0.2, "ether")

    assert tx_send.events["FundsTransfer"]["wallet"] == borrower
    assert tx_send.events["FundsTransfer"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_send.events["FundsTransfer"]["erc20TokenContract"] == erc20_contract


def test_send_funds_weth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    initial_balance = user_balance(erc20_contract, borrower)

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    tx_send = lending_pool_peripheral_contract.sendFundsWeth(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": loans_peripheral_contract}
    )

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.toWei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.toWei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.toWei(0.2, "ether")

    assert tx_send.events["FundsTransfer"]["wallet"] == borrower
    assert tx_send.events["FundsTransfer"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_send.events["FundsTransfer"]["erc20TokenContract"] == erc20_contract


@pytest.mark.require_network("ganache-mainnet-fork")
def test_receive_funds_wrong_sender_eth(lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the loans addr"):
        lending_pool_peripheral_contract.receiveFundsEth(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower, "value": Web3.toWei(0.25, "ether")}
        )


def test_receive_funds_wrong_sender_weth(erc20_contract, lending_pool_peripheral_contract, lending_pool_core_contract, borrower, contract_owner):
    erc20_contract.mint(borrower, Web3.toWei(0.25, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.25, "ether"), {"from": borrower})
    with brownie.reverts("msg.sender is not the loans addr"):
        lending_pool_peripheral_contract.receiveFundsWeth(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": borrower}
        )


@pytest.mark.require_network("ganache-mainnet-fork")
def test_receive_funds_insufficient_amount(lending_pool_peripheral_contract, loans_peripheral_contract, contract_owner, borrower,Smuggler):
    smuggler = Smuggler.deploy({'from': contract_owner})
    contract_owner.transfer(to=smuggler, amount=Web3.toWei(2, "ether"))
    smuggler.deliver(loans_peripheral_contract)
    with brownie.reverts("recv amount not match partials"):
        lending_pool_peripheral_contract.receiveFundsEth(
            borrower,
            Web3.toWei(0.2, "ether"),
            Web3.toWei(0.05, "ether"),
            {"from": loans_peripheral_contract, 'value': Web3.toWei(0.15, "ether")}
        )


def test_receive_funds_zero_value(lending_pool_peripheral_contract, loans_peripheral_contract, borrower):
    with brownie.reverts("amount should be higher than 0"):
        lending_pool_peripheral_contract.receiveFundsEth(
            borrower,
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": loans_peripheral_contract}
        )

    with brownie.reverts("amount should be higher than 0"):
        lending_pool_peripheral_contract.receiveFundsWeth(
            borrower,
            Web3.toWei(0, "ether"),
            Web3.toWei(0, "ether"),
            {"from": loans_peripheral_contract}
        )


@pytest.mark.require_network("ganache-mainnet-fork")
def test_receive_funds_eth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower,
    protocol_wallet,
    Smuggler
):
    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})

    lending_pool_peripheral_contract.sendFundsEth(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": loans_peripheral_contract}
    )

    contract_owner.transfer(to=borrower, amount=Web3.toWei(0.02, "ether"))

    smuggler = Smuggler.deploy({'from': contract_owner})
    contract_owner.transfer(to=smuggler, amount=Web3.toWei(1, "ether"))
    smuggler.deliver(loans_peripheral_contract)

    tx_receive = lending_pool_peripheral_contract.receiveFundsEth(
        borrower,
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": loans_peripheral_contract, 'value': Web3.toWei(0.22, "ether")}
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

    assert tx_receive.events["FundsReceipt"]["wallet"] == borrower
    assert tx_receive.events["FundsReceipt"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["investedAmount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["erc20TokenContract"] == erc20_contract
    assert tx_receive.events["FundsReceipt"]["fundsOrigin"] == "loan"


def test_receive_funds_weth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower,
    protocol_wallet
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.depositWeth(Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.sendFundsWeth(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": loans_peripheral_contract}
    )

    erc20_contract.mint(borrower, Web3.toWei(0.02, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.22, "ether"), {"from": borrower})
    tx_receive = lending_pool_peripheral_contract.receiveFundsWeth(
        borrower,
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": loans_peripheral_contract}
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

    assert tx_receive.events["FundsReceipt"]["wallet"] == borrower
    assert tx_receive.events["FundsReceipt"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["investedAmount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["erc20TokenContract"] == erc20_contract
    assert tx_receive.events["FundsReceipt"]["fundsOrigin"] == "loan"


@pytest.mark.require_network("ganache-mainnet-fork")
def test_receive_funds_multiple_lenders_weth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    loans_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    protocol_wallet
):
    contract_owner.transfer(to=investor, amount=Web3.toWei(1, "ether"))
    lending_pool_peripheral_contract.depositEth({"from": investor, 'value': Web3.toWei(1, "ether")})
    lending_pool_peripheral_contract.depositEth({"from": contract_owner, 'value': Web3.toWei(3, "ether")})

    lending_pool_peripheral_contract.sendFundsEth(
        borrower,
        Web3.toWei(0.2, "ether"),
        {"from": loans_peripheral_contract}
    )

    contract_owner.transfer(to=borrower, amount=Web3.toWei(0.22, "ether"))

    erc20_contract.mint(borrower, Web3.toWei(0.02, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(0.22, "ether"), {"from": borrower})
    tx_receive = lending_pool_peripheral_contract.receiveFundsWeth(
        borrower,
        Web3.toWei(0.2, "ether"),
        Web3.toWei(0.02, "ether"),
        {"from": loans_peripheral_contract}
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

    assert tx_receive.events["FundsReceipt"]["wallet"] == borrower
    assert tx_receive.events["FundsReceipt"]["amount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsPool"] == Web3.toWei(expectedPoolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["rewardsProtocol"] == Web3.toWei(expectedProtocolFees, "ether")
    assert tx_receive.events["FundsReceipt"]["investedAmount"] == Web3.toWei(0.2, "ether")
    assert tx_receive.events["FundsReceipt"]["erc20TokenContract"] == erc20_contract
    assert tx_receive.events["FundsReceipt"]["fundsOrigin"] == "loan"
