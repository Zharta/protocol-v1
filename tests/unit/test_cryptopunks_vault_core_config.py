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
def delegation_registry(delegation_registry_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return delegation_registry_contract.deploy()


@pytest.fixture(scope="module")
def cryptopunks_vault_core(cryptopunks_vault_core_contract, delegation_registry, cryptopunks_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return cryptopunks_vault_core_contract.deploy(cryptopunks_contract.deploy(), delegation_registry)


def test_initial_state(cryptopunks_vault_core, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert cryptopunks_vault_core.owner() == contract_owner


def test_propose_owner_wrong_sender(cryptopunks_vault_core, borrower):
    with boa.reverts("msg.sender is not the owner"):
        cryptopunks_vault_core.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(cryptopunks_vault_core, contract_owner):
    with boa.reverts("address it the zero address"):
        cryptopunks_vault_core.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(cryptopunks_vault_core, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        cryptopunks_vault_core.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(cryptopunks_vault_core, contract_owner, borrower):
    cryptopunks_vault_core.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(cryptopunks_vault_core, name="OwnerProposed")

    assert cryptopunks_vault_core.owner() == contract_owner
    assert cryptopunks_vault_core.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(cryptopunks_vault_core, contract_owner, borrower):
    cryptopunks_vault_core.proposeOwner(borrower, sender=contract_owner)
    with boa.reverts("proposed owner addr is the same"):
        cryptopunks_vault_core.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(cryptopunks_vault_core, contract_owner, borrower):
    cryptopunks_vault_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        cryptopunks_vault_core.claimOwnership(sender=contract_owner)


def test_claim_ownership(cryptopunks_vault_core, contract_owner, borrower):
    cryptopunks_vault_core.proposeOwner(borrower, sender=contract_owner)

    cryptopunks_vault_core.claimOwnership(sender=borrower)
    event = get_last_event(cryptopunks_vault_core, name="OwnershipTransferred")

    assert cryptopunks_vault_core.owner() == borrower
    assert cryptopunks_vault_core.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_collateral_vault_peripheral_address_wrong_sender(cryptopunks_vault_core, borrower):
    collateral_vault_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=borrower)


def test_set_collateral_vault_address_peripheral_zero_address(cryptopunks_vault_core, contract_owner):
    with boa.reverts("address is the zero addr"):
        cryptopunks_vault_core.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_peripheral_address(cryptopunks_vault_core, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()

    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)
    event = get_last_event(cryptopunks_vault_core, name="CollateralVaultPeripheralAddressSet")

    assert cryptopunks_vault_core.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral


