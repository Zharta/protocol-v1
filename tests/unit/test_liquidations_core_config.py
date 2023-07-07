from web3 import Web3
import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event

GRACE_PERIOD_DURATION = 172800  # 2 days
LENDER_PERIOD_DURATION = 604800  # 15 days
AUCTION_DURATION = 604800  # 15 days

PRINCIPAL = Web3.to_wei(1, "ether")
INTEREST_AMOUNT = Web3.to_wei(0.1, "ether")
APR = 200


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def investor():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc20():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def liquidations_core(liquidations_core_contract, erc20, contract_owner):
    with boa.env.prank(contract_owner):
        return liquidations_core_contract.deploy()


def test_initial_state(liquidations_core, contract_owner,):
    assert liquidations_core.owner() == contract_owner


def test_propose_owner_wrong_sender(liquidations_core, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_core.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(liquidations_core, contract_owner):
    with boa.reverts("address it the zero address"):
        liquidations_core.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(liquidations_core, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        liquidations_core.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(liquidations_core, contract_owner, borrower):
    liquidations_core.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(liquidations_core, name="OwnerProposed")

    assert liquidations_core.owner() == contract_owner
    assert liquidations_core.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(liquidations_core, contract_owner, borrower):
    liquidations_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        liquidations_core.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(liquidations_core, contract_owner, borrower):
    liquidations_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        liquidations_core.claimOwnership(sender=contract_owner)


def test_claim_ownership(liquidations_core, contract_owner, borrower):
    liquidations_core.proposeOwner(borrower, sender=contract_owner)

    liquidations_core.claimOwnership(sender=borrower)
    event = get_last_event(liquidations_core, name="OwnershipTransferred")

    assert liquidations_core.owner() == borrower
    assert liquidations_core.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_liquidations_peripheral_address_wrong_sender(liquidations_core, borrower):
    liquidations_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=borrower)


def test_set_liquidations_peripheral_address_zero_address(liquidations_core, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_core.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_liquidations_peripheral_address(liquidations_core, contract_owner):
    liquidations_peripheral = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)
    event = get_last_event(liquidations_core, name="LiquidationsPeripheralAddressSet")

    assert liquidations_core.liquidationsPeripheralAddress() == liquidations_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == liquidations_peripheral


def test_set_liquidations_peripheral_address_same_address(liquidations_core, contract_owner):
    liquidations_peripheral = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    assert liquidations_core.liquidationsPeripheralAddress() == liquidations_peripheral

    with boa.reverts("new value is the same"):
        liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)
