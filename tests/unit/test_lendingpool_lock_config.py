import boa
import pytest
from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc20():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def lending_pool_lock(lendingpool_lock_contract, erc20, contract_owner):
    with boa.env.prank(contract_owner):
        return lendingpool_lock_contract.deploy(erc20)


def test_initial_state(lending_pool_lock, erc20, contract_owner, protocol_wallet):
    assert lending_pool_lock.owner() == contract_owner
    assert lending_pool_lock.erc20TokenContract() == erc20


def test_propose_owner_wrong_sender(lending_pool_lock, borrower):
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_lock.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(lending_pool_lock, contract_owner):
    with boa.reverts("_address it the zero address"):
        lending_pool_lock.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(lending_pool_lock, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        lending_pool_lock.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(lending_pool_lock, contract_owner, borrower):
    lending_pool_lock.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(lending_pool_lock, name="OwnerProposed")

    assert lending_pool_lock.owner() == contract_owner
    assert lending_pool_lock.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(lending_pool_lock, contract_owner, borrower):
    lending_pool_lock.proposeOwner(borrower, sender=contract_owner)
    with boa.reverts("proposed owner addr is the same"):
        lending_pool_lock.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(lending_pool_lock, contract_owner, borrower):
    lending_pool_lock.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        lending_pool_lock.claimOwnership(sender=contract_owner)


def test_claim_ownership(lending_pool_lock, contract_owner, borrower):
    lending_pool_lock.proposeOwner(borrower, sender=contract_owner)

    lending_pool_lock.claimOwnership(sender=borrower)
    event = get_last_event(lending_pool_lock, name="OwnershipTransferred")

    assert lending_pool_lock.owner() == borrower
    assert lending_pool_lock.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_lending_pool_peripheral_address_wrong_sender(lending_pool_lock, investor):
    lending_pool_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        lending_pool_lock.setLendingPoolPeripheralAddress(lending_pool_peripheral, sender=investor)


def test_set_lending_pool_peripheral_address_zero_address(lending_pool_lock, contract_owner):
    with boa.reverts("address is the zero address"):
        lending_pool_lock.setLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_lending_pool_peripheral_address(lending_pool_lock, contract_owner):

    lending_pool_peripheral = boa.env.generate_address()
    lending_pool_lock.setLendingPoolPeripheralAddress(lending_pool_peripheral, sender=contract_owner)
    event = get_last_event(lending_pool_lock, name="LendingPoolPeripheralAddressSet")

    assert lending_pool_lock.lendingPoolPeripheral() == lending_pool_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == lending_pool_peripheral
