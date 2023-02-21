from decimal import Decimal
from web3 import Web3

import boa
import pytest
from ..conftest_base import ZERO_ADDRESS, get_last_event, get_events, checksummed


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
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract_aux, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="LoansPeripheralAddressSet")

    assert lending_pool_peripheral_contract.loansContract() == loans_peripheral_contract_aux.address
    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_peripheral_contract_aux.address

    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="LoansPeripheralAddressSet")

    assert lending_pool_peripheral_contract.loansContract() == loans_peripheral_contract.address
    assert event.currentValue == loans_peripheral_contract_aux.address
    assert event.newValue == loans_peripheral_contract.address


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(lending_pool_peripheral_contract, lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_peripheral_contract.owner() == contract_owner
    assert lending_pool_peripheral_contract.lendingPoolCoreContract() == lending_pool_core_contract.address
    assert lending_pool_peripheral_contract.erc20TokenContract() == erc20_contract.address
    assert lending_pool_peripheral_contract.protocolWallet() == protocol_wallet
    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE
    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY
    assert lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolDeprecated()
    assert not lending_pool_peripheral_contract.isPoolInvesting()
    assert not lending_pool_peripheral_contract.whitelistEnabled()


def test_propose_owner_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("_address it the zero address"):
        lending_pool_peripheral_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        lending_pool_peripheral_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="OwnerProposed")

    assert lending_pool_peripheral_contract.proposedOwner() == borrower
    assert lending_pool_peripheral_contract.owner() == contract_owner

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, sender=contract_owner)
    
    with boa.reverts("proposed owner addr is the same"):
        lending_pool_peripheral_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        lending_pool_peripheral_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(lending_pool_peripheral_contract, contract_owner, borrower):
    lending_pool_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    lending_pool_peripheral_contract.claimOwnership(sender=borrower)
    event = get_last_event(lending_pool_peripheral_contract, name="OwnershipTransferred")

    assert lending_pool_peripheral_contract.owner() == borrower
    assert lending_pool_peripheral_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_change_max_capital_efficiency_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY, sender=borrower)

def test_change_max_capital_efficiency_excess_value(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("capital eff exceeds 10000 bps"):
        lending_pool_peripheral_contract.changeMaxCapitalEfficiency(10001, sender=contract_owner)


def test_change_max_capital_efficiency(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY + 1000, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="MaxCapitalEfficiencyChanged")

    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY + 1000
    assert event.currentValue == MAX_CAPITAL_EFFICIENCY
    assert event.newValue == MAX_CAPITAL_EFFICIENCY + 1000

    lending_pool_peripheral_contract.changeMaxCapitalEfficiency(MAX_CAPITAL_EFFICIENCY, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="MaxCapitalEfficiencyChanged")

    assert lending_pool_peripheral_contract.maxCapitalEfficienty() == MAX_CAPITAL_EFFICIENCY
    assert event.currentValue == MAX_CAPITAL_EFFICIENCY + 1000
    assert event.newValue == MAX_CAPITAL_EFFICIENCY


def test_change_protocol_wallet_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeProtocolWallet(borrower, sender=borrower)


def test_change_protocol_wallet_zero_address(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.changeProtocolWallet(ZERO_ADDRESS, sender=contract_owner)


def test_change_protocol_wallet(lending_pool_peripheral_contract, contract_owner, protocol_wallet):
    lending_pool_peripheral_contract.changeProtocolWallet(contract_owner, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="ProtocolWalletChanged")

    assert lending_pool_peripheral_contract.protocolWallet() == contract_owner
    assert event.currentValue == protocol_wallet
    assert event.newValue == contract_owner

    lending_pool_peripheral_contract.changeProtocolWallet(protocol_wallet, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="ProtocolWalletChanged")

    assert lending_pool_peripheral_contract.protocolWallet() == protocol_wallet
    assert event.currentValue == contract_owner
    assert event.newValue == protocol_wallet


def test_change_protocol_fees_share_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE + 1000, sender=borrower)


def test_change_protocol_fees_share_excess_value(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("fees share exceeds 10000 bps"):
        lending_pool_peripheral_contract.changeProtocolFeesShare(10001, sender=contract_owner)


def test_change_protocol_fees_share(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE + 1000, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="ProtocolFeesShareChanged")

    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE + 1000
    assert event.currentValue == PROTOCOL_FEES_SHARE
    assert event.newValue == PROTOCOL_FEES_SHARE + 1000

    lending_pool_peripheral_contract.changeProtocolFeesShare(PROTOCOL_FEES_SHARE, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="ProtocolFeesShareChanged")

    assert lending_pool_peripheral_contract.protocolFeesShare() == PROTOCOL_FEES_SHARE
    assert event.currentValue == PROTOCOL_FEES_SHARE + 1000
    assert event.newValue == PROTOCOL_FEES_SHARE


def test_change_loans_peripheral_address_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.setLoansPeripheralAddress(borrower, sender=borrower)


def test_change_loans_peripheral_address_zero_address(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.setLoansPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_change_loans_peripheral_address_not_contract(lending_pool_peripheral_contract, borrower, contract_owner):
    with boa.reverts("_address is not a contract"):
        lending_pool_peripheral_contract.setLoansPeripheralAddress(borrower, sender=contract_owner)


def test_change_whitelist_status_wrong_sender(lending_pool_peripheral_contract, investor):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=investor)


def test_change_whitelist_status_same_status(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("new value is the same"):
        lending_pool_peripheral_contract.changeWhitelistStatus(False, sender=contract_owner)


def test_change_whitelist_status(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="WhitelistStatusChanged")

    assert lending_pool_peripheral_contract.whitelistEnabled()
    assert event.value

    lending_pool_peripheral_contract.changeWhitelistStatus(False, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="WhitelistStatusChanged")

    assert not lending_pool_peripheral_contract.whitelistEnabled()
    assert not event.value


def test_add_whitelisted_address_wrong_sender(lending_pool_peripheral_contract, investor):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=investor)


def test_add_whitelisted_address_zero_address(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.addWhitelistedAddress(ZERO_ADDRESS, sender=contract_owner)


def test_add_whitelisted_address_whitelist_disabled(lending_pool_peripheral_contract, contract_owner, investor):
    with boa.reverts("whitelist is disabled"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=contract_owner)


def test_add_whitelisted_address(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="WhitelistAddressAdded")

    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)
    assert event.value == investor


def test_add_whitelisted_address_already_whitelisted(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    with boa.reverts("address is already whitelisted"):
        lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=contract_owner)


def test_remove_whitelisted_address_wrong_sender(lending_pool_peripheral_contract, investor):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, sender=investor)


def test_remove_whitelisted_address_zero_address(lending_pool_peripheral_contract, contract_owner):
    with boa.reverts("_address is the zero address"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(ZERO_ADDRESS, sender=contract_owner)


def test_remove_whitelisted_address_whitelist_disabled(lending_pool_peripheral_contract, contract_owner, investor):
    with boa.reverts("whitelist is disabled"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, sender=contract_owner)


def test_remove_whitelisted_address_not_whitelisted(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistEnabled()

    with boa.reverts("address is not whitelisted"):
        lending_pool_peripheral_contract.removeWhitelistedAddress(investor, sender=contract_owner)


def test_remove_whitelisted_address(lending_pool_peripheral_contract, contract_owner, investor):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    lending_pool_peripheral_contract.removeWhitelistedAddress(investor, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="WhitelistAddressRemoved")

    assert not lending_pool_peripheral_contract.whitelistedAddresses(investor)
    assert event.value == investor


def test_change_pool_status_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.changePoolStatus(False, sender=borrower)


def test_change_pool_status(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changePoolStatus(False, sender=contract_owner)
    contract_status_event = get_last_event(lending_pool_peripheral_contract, name="ContractStatusChanged")
    investing_status_event = get_last_event(lending_pool_peripheral_contract, name="InvestingStatusChanged")

    assert not lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolInvesting()

    assert not contract_status_event.value
    assert not investing_status_event.value


def test_change_pool_status_again(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.changePoolStatus(False, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="ContractStatusChanged")

    assert not event.value

    lending_pool_peripheral_contract.changePoolStatus(True, sender=contract_owner)
    event = get_last_event(lending_pool_peripheral_contract, name="ContractStatusChanged")

    assert lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolInvesting()
    assert event.value


def test_deprecate_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_peripheral_contract.deprecate(sender=borrower)


def test_deprecate(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.deprecate(sender=contract_owner)

    assert not get_last_event(lending_pool_peripheral_contract, name="ContractStatusChanged").value
    assert not get_last_event(lending_pool_peripheral_contract, name="InvestingStatusChanged").value
    assert get_last_event(lending_pool_peripheral_contract, name="ContractDeprecated")

    assert lending_pool_peripheral_contract.isPoolDeprecated()
    assert not lending_pool_peripheral_contract.isPoolActive()
    assert not lending_pool_peripheral_contract.isPoolInvesting()



def test_deprecate_already_deprecated(lending_pool_peripheral_contract, contract_owner):
    lending_pool_peripheral_contract.deprecate(sender=contract_owner)

    with boa.reverts("pool is already deprecated"):
        lending_pool_peripheral_contract.deprecate(sender=contract_owner)


def test_default_fn_wrong_sender(lending_pool_peripheral_contract, borrower):
    with boa.env.prank(borrower):
        with boa.reverts():
            boa.eval(f"send({lending_pool_peripheral_contract.address}, 1)")


def test_deposit_deprecated(lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_peripheral_contract.deprecate(sender=contract_owner)

    with boa.reverts("pool is deprecated, withdraw"):
        lending_pool_peripheral_contract.depositEth(sender=investor, value=10**18)


def test_deposit_inactive(lending_pool_peripheral_contract, investor, contract_owner):
    lending_pool_peripheral_contract.changePoolStatus(False, sender=contract_owner)

    with boa.reverts("pool is not active right now"):
        lending_pool_peripheral_contract.depositEth(sender=investor, value=10**18)


def test_deposit_zero_investment(lending_pool_peripheral_contract, investor):
    with boa.reverts("_amount has to be higher than 0"):
        lending_pool_peripheral_contract.depositEth(sender=investor, value=0)


def test_deposit_pool_share_surpassed(lending_pool_peripheral_contract, liquidity_controls_contract, investor, contract_owner):
    liquidity_controls_contract.changeMaxPoolShareConditions(True, MAX_POOL_SHARE, sender=contract_owner)
    with boa.reverts("max pool share surpassed"):
        lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))


def test_deposit_insufficient_amount_allowed(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    investor,
    contract_owner
):
    # erc20_contract.mint(investor, Web3.to_wei(0.5, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(0.5, "ether"), sender=investor)

    with boa.reverts("not enough funds allowed"):
        lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)


def test_deposit_not_whitelisted(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    investor,
    contract_owner
):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistEnabled()

    deposit_amount = Web3.to_wei(1, "ether")

    # erc20_contract.mint(investor, deposit_amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, deposit_amount, sender=investor)

    with boa.reverts("msg.sender is not whitelisted"):
        lending_pool_peripheral_contract.depositEth(sender=investor, value= deposit_amount)


def test_deposit_whitelisted(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    investor,
    contract_owner
):
    lending_pool_peripheral_contract.changeWhitelistStatus(True, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistEnabled()

    lending_pool_peripheral_contract.addWhitelistedAddress(investor, sender=contract_owner)
    assert lending_pool_peripheral_contract.whitelistedAddresses(investor)

    # contract_owner.transfer(to=investor, amount=Web3.to_wei(1, "ether"))

    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))
    event = get_last_event(lending_pool_peripheral_contract, name="Deposit")

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == Web3.to_wei(1, "ether")
    assert investor_funds[1] == Web3.to_wei(1, "ether")
    assert investor_funds[2] == 0
    assert investor_funds[3] == Web3.to_wei(1, "ether")
    assert investor_funds[4] == True

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    # First event is the deposit of the ETH in the WETH contract
    assert event.wallet == investor
    assert event.amount == Web3.to_wei(1, "ether")
    assert event.erc20TokenContract == erc20_contract.address


def test_deposit_eth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount = Web3.to_wei(1, "ether")
    # contract_owner.transfer(to=investor, amount=amount)
    lending_pool_peripheral_contract.depositEth(sender=investor, value= amount)
    event = get_last_event(lending_pool_peripheral_contract, name="Deposit")

    chain_time = boa.eval("block.timestamp")

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == amount
    assert investor_funds[1] == amount
    assert investor_funds[2] == 0
    assert investor_funds[3] == amount
    assert investor_funds[4] == True

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period[0] <= chain_time + LOCK_PERIOD_DURATION + 10  # 10s of buffer
    assert lock_period[1] == amount

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    # First event is the deposit of the ETH in the WETH contract
    assert event.wallet == investor
    assert event.amount == amount
    assert event.erc20TokenContract == erc20_contract.address


def test_deposit_weth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount = Web3.to_wei(1, "ether")
    # erc20_contract.mint(investor, amount, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, amount, sender=investor)

    lending_pool_peripheral_contract.depositWeth(amount, sender=investor)
    event = get_last_event(lending_pool_peripheral_contract, name="Deposit")

    chain_time = boa.eval("block.timestamp")

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == amount
    assert investor_funds[1] == amount
    assert investor_funds[2] == 0
    assert investor_funds[3] == amount
    assert investor_funds[4] == True

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period[0] <= chain_time + LOCK_PERIOD_DURATION + 10  # 10s of buffer
    assert lock_period[1] == amount

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert event.wallet == investor
    assert event.amount == amount
    assert event.erc20TokenContract == erc20_contract.address


def test_deposit_twice(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount1 = Web3.to_wei(1, "ether")
    # contract_owner.transfer(to=investor, amount=amount1)
    lending_pool_peripheral_contract.depositEth(sender=investor, value= amount1)
    event_deposit_1 = get_last_event(lending_pool_peripheral_contract, name="Deposit")

    chain_time = boa.eval("block.timestamp")

    boa.env.time_travel(seconds=LOCK_PERIOD_DURATION // 2)

    amount2 = Web3.to_wei(0.5, "ether")
    # contract_owner.transfer(to=investor, amount=amount2)
    lending_pool_peripheral_contract.depositEth(sender=investor, value= amount2)
    event_deposit_2 = get_last_event(lending_pool_peripheral_contract, name="Deposit")

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == amount1 + amount2
    assert investor_funds[1] == amount1 + amount2

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period[0] <= chain_time + LOCK_PERIOD_DURATION + 10  # 10s of buffer
    assert lock_period[1] == amount1 + amount2

    assert lending_pool_core_contract.fundsAvailable() == amount1 + amount2
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    # First event is the deposit of the ETH in the WETH contract
    assert event_deposit_1.wallet == investor
    assert event_deposit_1.amount == amount1
    assert event_deposit_1.erc20TokenContract == erc20_contract.address

    # First event is the deposit of the ETH in the WETH contract
    assert event_deposit_2.wallet == investor
    assert event_deposit_2.amount == amount2
    assert event_deposit_2.erc20TokenContract == erc20_contract.address


def test_deposit_max_pool_share_enabled(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    # erc20_contract.mint(contract_owner, Web3.to_wei(3, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(3, "ether"), sender=contract_owner)

    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(3, "ether"), sender=contract_owner)

    liquidity_controls_contract.changeMaxPoolShareConditions(True, 4000, sender=contract_owner)

    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)
    event = get_last_event(lending_pool_peripheral_contract, name="Deposit")

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == Web3.to_wei(1, "ether")
    assert investor_funds[1] == Web3.to_wei(1, "ether")
    assert investor_funds[2] == 0
    assert investor_funds[3] == Web3.to_wei(1, "ether")
    assert investor_funds[4] == True

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(4, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0

    assert lending_pool_peripheral_contract.isPoolInvesting()

    assert event.wallet == investor
    assert event.amount == Web3.to_wei(1, "ether")
    assert event.erc20TokenContract == erc20_contract.address


def test_withdraw_zero_amount(lending_pool_peripheral_contract, investor):
    with boa.reverts("_amount has to be higher than 0"):
        lending_pool_peripheral_contract.withdrawEth(0, sender=investor)


def test_withdraw_noinvestment(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, investor, contract_owner):
    with boa.reverts("_amount more than withdrawable"):
        lending_pool_peripheral_contract.withdrawEth(Web3.to_wei(1, "ether"), sender=investor)


def test_withdraw_insufficient_investment(
    lending_pool_peripheral_contract,
    investor,
    contract_owner
):
    # contract_owner.transfer(to=investor, amount=Web3.to_wei(1, "ether"))
    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))

    with boa.reverts("_amount more than withdrawable"):
        lending_pool_peripheral_contract.withdrawEth(Web3.to_wei(1.5, "ether"), sender=investor)

    with boa.reverts("_amount more than withdrawable"):
        lending_pool_peripheral_contract.withdrawWeth(Web3.to_wei(1.5, "ether"), sender=investor)


def test_withdraw(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    initial_balance = boa.env.get_balance(investor)

    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))
    assert boa.env.get_balance(investor) == initial_balance - Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1, "ether")

    lending_pool_peripheral_contract.withdrawEth(Web3.to_wei(1, "ether"), sender=investor)
    event = get_events(lending_pool_peripheral_contract, name="Withdrawal")[-2]  # last Withdrawal comes from WETH9

    assert boa.env.get_balance(investor) == initial_balance
    assert lending_pool_core_contract.fundsAvailable() == 0

    investor_funds = lending_pool_core_contract.funds(investor)
    assert investor_funds[0] == 0
    assert investor_funds[1] == Web3.to_wei(1, "ether")
    assert investor_funds[2] == Web3.to_wei(1, "ether")
    assert investor_funds[3] == 0
    assert investor_funds[4] == False

    assert event.wallet == investor
    assert event.amount == Web3.to_wei(1, "ether")
    assert event.erc20TokenContract == erc20_contract.address


def test_withdraw_within_lock_period(
    lending_pool_peripheral_contract,
    liquidity_controls_contract,
    investor,
    contract_owner
):
    # contract_owner.transfer(to=investor, amount=Web3.to_wei(2, "ether"))
    liquidity_controls_contract.changeLockPeriodConditions(True, LOCK_PERIOD_DURATION*2, sender=contract_owner)
    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))

    with boa.reverts("withdraw within lock period"):
        lending_pool_peripheral_contract.withdrawEth(Web3.to_wei(1, "ether"), sender=investor)

    with boa.reverts("withdraw within lock period"):
        lending_pool_peripheral_contract.withdrawWeth(Web3.to_wei(1, "ether"), sender=investor)


def test_withdraw_within_lock_period_within_amount(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    amount1 = Web3.to_wei(1, "ether")
    amount2 = Web3.to_wei(2, "ether")
    # erc20_contract.mint(investor, amount1 + amount2, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, amount1 + amount2, sender=investor)

    liquidity_controls_contract.changeLockPeriodConditions(True, LOCK_PERIOD_DURATION, sender=contract_owner)
    lending_pool_peripheral_contract.depositWeth(amount1, sender=investor)

    # chain.mine(blocks=1, timedelta=LOCK_PERIOD_DURATION * 2)
    boa.env.time_travel(seconds=LOCK_PERIOD_DURATION * 2)

    lending_pool_peripheral_contract.depositWeth(amount2, sender=investor)
    lending_pool_peripheral_contract.withdrawWeth(amount1, sender=investor)

    lock_period = lending_pool_lock_contract.investorLocks(investor)
    assert lock_period[1] == amount2


def test_withdraw_out_of_lock_period(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    liquidity_controls_contract,
    erc20_contract,
    investor,
    contract_owner
):
    # erc20_contract.mint(investor, Web3.to_wei(2, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(2, "ether"), sender=investor)

    liquidity_controls_contract.changeLockPeriodConditions(True, LOCK_PERIOD_DURATION*2, sender=contract_owner)

    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    # chain.mine(blocks=1, timedelta=LOCK_PERIOD_DURATION * 2)
    boa.env.time_travel(seconds=LOCK_PERIOD_DURATION * 2)

    lending_pool_peripheral_contract.withdrawWeth(Web3.to_wei(1, "ether"), sender=investor)


def test_send_funds_deprecated(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, contract_owner, investor, borrower):
    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)
    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.deprecate(sender=contract_owner)

    with boa.reverts("pool is deprecated"):
        lending_pool_peripheral_contract.sendFundsWeth(borrower, Web3.to_wei(1, "ether"), sender=contract_owner)


def test_send_funds_inactive(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, contract_owner, investor, borrower):
    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)
    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.changePoolStatus(False, sender=contract_owner)

    with boa.reverts("pool is inactive"):
        lending_pool_peripheral_contract.sendFundsWeth(borrower, Web3.to_wei(1, "ether"), sender=contract_owner)


def test_send_funds_wrong_sender(lending_pool_peripheral_contract, lending_pool_core_contract, liquidity_controls_contract, erc20_contract, contract_owner, investor, borrower):
    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)
    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    with boa.reverts("msg.sender is not the loans addr"):
        lending_pool_peripheral_contract.sendFundsWeth(borrower, Web3.to_wei(1, "ether"), sender=investor)


def test_send_funds_zero_amount(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    loans_peripheral_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)
    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))

    with boa.reverts("_amount has to be higher than 0"):
        lending_pool_peripheral_contract.sendFundsEth(
            borrower,
            Web3.to_wei(0, "ether"),
            sender=loans_peripheral_contract.address
        )


def test_send_funds_wrong_amount(
    lending_pool_peripheral_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    # contract_owner.transfer(to=investor, amount=Web3.to_wei(1, "ether"))
    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))

    with boa.reverts("insufficient liquidity"):
        lending_pool_peripheral_contract.sendFundsEth(
            borrower,
            Web3.to_wei(2, "ether"),
            sender=loans_peripheral_contract.address
        )


def test_send_funds_insufficient_funds_to_lend(
    lending_pool_peripheral_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    # contract_owner.transfer(to=investor, amount=Web3.to_wei(1, "ether"))
    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))

    with boa.reverts("insufficient liquidity"):
        tx_send = lending_pool_peripheral_contract.sendFundsEth(
            borrower,
            Web3.to_wei(0.8, "ether"),
            sender=loans_peripheral_contract.address
        )


def test_send_funds_eth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower
):
    initial_balance = boa.env.get_balance(borrower)

    # contract_owner.transfer(to=investor, amount=Web3.to_wei(1, "ether"))

    lending_pool_peripheral_contract.depositEth(sender=investor, value= Web3.to_wei(1, "ether"))

    lending_pool_peripheral_contract.sendFundsEth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(lending_pool_peripheral_contract, name="FundsTransfer")

    assert boa.env.get_balance(borrower) == initial_balance + Web3.to_wei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.to_wei(0.2, "ether")

    assert event.wallet == borrower
    assert event.amount == Web3.to_wei(0.2, "ether")
    assert event.erc20TokenContract == erc20_contract.address


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

    # erc20_contract.mint(investor, Web3.to_wei(1, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.sendFundsWeth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(lending_pool_peripheral_contract, name="FundsTransfer")

    assert user_balance(erc20_contract, borrower) == initial_balance + Web3.to_wei(0.2, "ether")
    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(0.8, "ether")
    assert lending_pool_core_contract.fundsInvested() == Web3.to_wei(0.2, "ether")

    assert event.wallet == borrower
    assert event.amount == Web3.to_wei(0.2, "ether")
    assert event.erc20TokenContract == erc20_contract.address


def test_receive_funds_wrong_sender_eth(lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the loans addr"):
        lending_pool_peripheral_contract.receiveFundsEth(
            borrower,
            Web3.to_wei(0.2, "ether"),
            Web3.to_wei(0.05, "ether"),
            sender=borrower,
            value=Web3.to_wei(0.25, "ether")
        )


def test_receive_funds_wrong_sender_weth(erc20_contract, lending_pool_peripheral_contract, lending_pool_core_contract, borrower, contract_owner):
    # erc20_contract.mint(borrower, Web3.to_wei(0.25, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(0.25, "ether"), sender=borrower)
    with boa.reverts("msg.sender is not the loans addr"):
        lending_pool_peripheral_contract.receiveFundsWeth(
            borrower,
            Web3.to_wei(0.2, "ether"),
            Web3.to_wei(0.05, "ether"),
            sender=borrower
        )


def test_receive_funds_insufficient_amount(
    lending_pool_peripheral_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower
):
    boa.env.set_balance(loans_peripheral_contract.address, Web3.to_wei(2, "ether"))
    with boa.reverts("recv amount not match partials"):
        lending_pool_peripheral_contract.receiveFundsEth(
            borrower,
            Web3.to_wei(0.2, "ether"),
            Web3.to_wei(0.05, "ether"),
            sender=loans_peripheral_contract.address,
            value=Web3.to_wei(0.15, "ether")
        )


def test_receive_funds_zero_value(lending_pool_peripheral_contract, loans_peripheral_contract, borrower):
    with boa.reverts("amount should be higher than 0"):
        lending_pool_peripheral_contract.receiveFundsEth(
            borrower,
            Web3.to_wei(0, "ether"),
            Web3.to_wei(0, "ether"),
            sender=loans_peripheral_contract.address
        )

    with boa.reverts("amount should be higher than 0"):
        lending_pool_peripheral_contract.receiveFundsWeth(
            borrower,
            Web3.to_wei(0, "ether"),
            Web3.to_wei(0, "ether"),
            sender=loans_peripheral_contract.address
        )


def test_receive_funds_eth(
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    loans_peripheral_contract,
    contract_owner,
    investor,
    borrower,
    protocol_wallet,
):
    initial_protocol_balance = user_balance(erc20_contract, protocol_wallet)

    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    lending_pool_peripheral_contract.sendFundsEth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=loans_peripheral_contract.address
    )

    boa.env.set_balance(loans_peripheral_contract.address, 10**18)
    lending_pool_peripheral_contract.receiveFundsEth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        Web3.to_wei(0.02, "ether"),
        sender=loans_peripheral_contract.address,
        value= Web3.to_wei(0.22, "ether")
    )
    event = get_last_event(lending_pool_peripheral_contract, name="FundsReceipt")

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1 + expectedPoolFees, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0
    assert lending_pool_core_contract.totalFundsInvested() == Web3.to_wei(0.2, "ether")

    assert lending_pool_core_contract.totalRewards() == Web3.to_wei(expectedPoolFees, "ether")

    assert lending_pool_core_contract.funds(investor)[3] == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == Web3.to_wei(1 + expectedPoolFees, "ether")

    assert user_balance(erc20_contract, protocol_wallet) == initial_protocol_balance + Web3.to_wei(expectedProtocolFees, "ether")
    assert user_balance(erc20_contract, lending_pool_core_contract) == Web3.to_wei(1 + expectedPoolFees, "ether")

    assert event.wallet == borrower
    assert event.amount == Web3.to_wei(0.2, "ether")
    assert event.rewardsPool == Web3.to_wei(expectedPoolFees, "ether")
    assert event.rewardsProtocol == Web3.to_wei(expectedProtocolFees, "ether")
    assert event.investedAmount == Web3.to_wei(0.2, "ether")
    assert event.erc20TokenContract == erc20_contract.address
    assert event.fundsOrigin == "loan"


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
    initial_protocol_balance = user_balance(erc20_contract, protocol_wallet)

    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(1, "ether"), sender=investor)
    lending_pool_peripheral_contract.depositWeth(Web3.to_wei(1, "ether"), sender=investor)

    lending_pool_peripheral_contract.sendFundsWeth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=loans_peripheral_contract.address
    )

    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(0.22, "ether"), sender=borrower)
    lending_pool_peripheral_contract.receiveFundsWeth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        Web3.to_wei(0.02, "ether"),
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(lending_pool_peripheral_contract, name="FundsReceipt")

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(1 + expectedPoolFees, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0
    assert lending_pool_core_contract.totalFundsInvested() == Web3.to_wei(0.2, "ether")

    assert lending_pool_core_contract.totalRewards() == Web3.to_wei(expectedPoolFees, "ether")

    assert lending_pool_core_contract.funds(investor)[3] == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == Web3.to_wei(1 + expectedPoolFees, "ether")

    assert user_balance(erc20_contract, protocol_wallet) == initial_protocol_balance + Web3.to_wei(expectedProtocolFees, "ether")
    assert user_balance(erc20_contract, lending_pool_core_contract) == Web3.to_wei(1 + expectedPoolFees, "ether")

    assert event.wallet == borrower
    assert event.amount == Web3.to_wei(0.2, "ether")
    assert event.rewardsPool == Web3.to_wei(expectedPoolFees, "ether")
    assert event.rewardsProtocol == Web3.to_wei(expectedProtocolFees, "ether")
    assert event.investedAmount == Web3.to_wei(0.2, "ether")
    assert event.erc20TokenContract == erc20_contract.address
    assert event.fundsOrigin == "loan"


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
    initial_protocol_balance = user_balance(erc20_contract, protocol_wallet)

    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))
    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value=Web3.to_wei(3, "ether"))

    lending_pool_peripheral_contract.sendFundsEth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        sender=loans_peripheral_contract.address
    )

    # contract_owner.transfer(to=borrower, amount=Web3.to_wei(0.22, "ether"))

    # erc20_contract.mint(borrower, Web3.to_wei(0.02, "ether"), sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, Web3.to_wei(0.22, "ether"), sender=borrower)
    lending_pool_peripheral_contract.receiveFundsWeth(
        borrower,
        Web3.to_wei(0.2, "ether"),
        Web3.to_wei(0.02, "ether"),
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(lending_pool_peripheral_contract, name="FundsReceipt")

    expectedProtocolFees = Decimal(0.02) * Decimal(PROTOCOL_FEES_SHARE) / Decimal(10000)
    expectedPoolFees = Decimal(0.02) - expectedProtocolFees

    assert lending_pool_core_contract.fundsAvailable() == Web3.to_wei(4 + expectedPoolFees, "ether")
    assert lending_pool_core_contract.fundsInvested() == 0
    assert lending_pool_core_contract.totalFundsInvested() == Web3.to_wei(0.2, "ether")

    assert lending_pool_core_contract.totalRewards() == Web3.to_wei(expectedPoolFees, "ether")

    expectedLenderOneRewards = expectedPoolFees * Decimal(1) / Decimal(4)
    expectedLenderTwoRewards = expectedPoolFees * Decimal(3) / Decimal(4)

    assert lending_pool_core_contract.funds(investor)[3] == Web3.to_wei(1, "ether")
    assert lending_pool_core_contract.funds(contract_owner)[3] == Web3.to_wei(3, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(investor) == Web3.to_wei(1 + expectedLenderOneRewards, "ether")
    assert lending_pool_core_contract.computeWithdrawableAmount(contract_owner) == Web3.to_wei(3 + expectedLenderTwoRewards, "ether")

    assert user_balance(erc20_contract, protocol_wallet) == initial_protocol_balance + Web3.to_wei(expectedProtocolFees, "ether")
    assert user_balance(erc20_contract, lending_pool_core_contract) == Web3.to_wei(4 + expectedPoolFees, "ether")

    assert event.wallet == borrower
    assert event.amount == Web3.to_wei(0.2, "ether")
    assert event.rewardsPool == Web3.to_wei(expectedPoolFees, "ether")
    assert event.rewardsProtocol == Web3.to_wei(expectedProtocolFees, "ether")
    assert event.investedAmount == Web3.to_wei(0.2, "ether")
    assert event.erc20TokenContract == erc20_contract.address
    assert event.fundsOrigin == "loan"
