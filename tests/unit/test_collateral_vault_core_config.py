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
def collateral_vault_core(collateral_vault_core_contract, genesis, contract_owner):
    with boa.env.prank(contract_owner):
        return collateral_vault_core_contract.deploy(boa.env.generate_address())


def test_initial_state(collateral_vault_core, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_core.owner() == contract_owner


def test_propose_owner_wrong_sender(collateral_vault_core, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_core.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(collateral_vault_core, contract_owner):
    with boa.reverts("address it the zero address"):
        collateral_vault_core.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(collateral_vault_core, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        collateral_vault_core.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(collateral_vault_core, contract_owner, borrower):
    collateral_vault_core.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(collateral_vault_core, name="OwnerProposed")

    assert collateral_vault_core.owner() == contract_owner
    assert collateral_vault_core.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(collateral_vault_core, contract_owner, borrower):
    collateral_vault_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        collateral_vault_core.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(collateral_vault_core, contract_owner, borrower):
    collateral_vault_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        collateral_vault_core.claimOwnership(sender=contract_owner)


def test_claim_ownership(collateral_vault_core, contract_owner, borrower):
    collateral_vault_core.proposeOwner(borrower, sender=contract_owner)

    collateral_vault_core.claimOwnership(sender=borrower)
    event = get_last_event(collateral_vault_core, name="OwnershipTransferred")

    assert collateral_vault_core.owner() == borrower
    assert collateral_vault_core.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_collateral_vault_peripheral_address_wrong_sender(collateral_vault_core, borrower):
    collateral_vault_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=borrower)


def test_set_collateral_vault_address_peripheral_zero_address(collateral_vault_core, contract_owner):
    with boa.reverts("address is the zero addr"):
        collateral_vault_core.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_peripheral_address(collateral_vault_core, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)
    event = get_last_event(collateral_vault_core, name="CollateralVaultPeripheralAddressSet")

    assert collateral_vault_core.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral


def test_set_collateral_vault_address_peripheral_same_address(collateral_vault_core, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    assert collateral_vault_core.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    with boa.reverts("new value is the same"):
        collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)
