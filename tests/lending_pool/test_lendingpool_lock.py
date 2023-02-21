import boa
from datetime import datetime as dt
from ..conftest_base import ZERO_ADDRESS, get_last_event, checksummed

LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


def test_set_lending_pool_peripheral_address(lending_pool_lock_contract, lending_pool_peripheral_contract, contract_owner):
    lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
    event = get_last_event(lending_pool_lock_contract, name="LendingPoolPeripheralAddressSet")

    assert lending_pool_lock_contract.lendingPoolPeripheral() == lending_pool_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == lending_pool_peripheral_contract.address


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(lending_pool_lock_contract, erc20_contract, contract_owner, protocol_wallet):
    # Check if the constructor of the contract is set up properly
    assert lending_pool_lock_contract.owner() == contract_owner
    assert lending_pool_lock_contract.erc20TokenContract() == erc20_contract.address


def test_propose_owner_wrong_sender(lending_pool_lock_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_lock_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(lending_pool_lock_contract, contract_owner):
    with boa.reverts("_address it the zero address"):
        lending_pool_lock_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(lending_pool_lock_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        lending_pool_lock_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(lending_pool_lock_contract, name="OwnerProposed")

    assert lending_pool_lock_contract.owner() == contract_owner
    assert lending_pool_lock_contract.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, sender=contract_owner)
    with boa.reverts("proposed owner addr is the same"):
        lending_pool_lock_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        lending_pool_lock_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(lending_pool_lock_contract, contract_owner, borrower):
    lending_pool_lock_contract.proposeOwner(borrower, sender=contract_owner)

    lending_pool_lock_contract.claimOwnership(sender=borrower)
    event = get_last_event(lending_pool_lock_contract, name="OwnershipTransferred")

    assert lending_pool_lock_contract.owner() == borrower
    assert lending_pool_lock_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_lending_pool_peripheral_address_wrong_sender(
    lending_pool_lock_contract,
    lending_pool_peripheral_contract,
    investor
):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=investor)


def test_set_lending_pool_peripheral_address_zero_address(lending_pool_lock_contract, contract_owner):
    with boa.reverts("address is the zero address"):
        lending_pool_lock_contract.setLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_investor_lock_wrong_sender(lending_pool_lock_contract, lending_pool_peripheral_contract, investor):
    lockPeriodEnd = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_lock_contract.setInvestorLock(
            investor,
            10**18,
            lockPeriodEnd,
            sender=investor
        )


def test_set_investor_lock(lending_pool_lock_contract, lending_pool_peripheral_contract, investor):
    lockPeriodEnd = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    lockPeriodAmount = 10**18
    lending_pool_lock_contract.setInvestorLock(
        investor,
        lockPeriodAmount,
        lockPeriodEnd,
        sender=lending_pool_peripheral_contract.address
    )

    lock = lending_pool_lock_contract.investorLocks(investor)
    assert lock[0] == lockPeriodEnd
    assert lock[1] == lockPeriodAmount
