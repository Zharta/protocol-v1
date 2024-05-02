import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module")
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def delegation_registry(delegation_registry_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return delegation_registry_contract.deploy()


@pytest.fixture(scope="module")
def collateral_vault_core(collateral_vault_core_contract, delegation_registry, contract_owner):
    with boa.env.prank(contract_owner):
        return collateral_vault_core_contract.deploy(delegation_registry.address)


@pytest.fixture(scope="module")
def collateral_vault_peripheral(collateral_vault_peripheral_contract, collateral_vault_core, contract_owner):
    with boa.env.prank(contract_owner):
        return collateral_vault_peripheral_contract.deploy(collateral_vault_core.address)


def test_initial_state(collateral_vault_peripheral, collateral_vault_core, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_peripheral.owner() == contract_owner
    assert collateral_vault_peripheral.collateralVaultCoreDefaultAddress() == collateral_vault_core.address


def test_propose_owner_wrong_sender(collateral_vault_peripheral, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(collateral_vault_peripheral, contract_owner):
    with boa.reverts("address it the zero address"):
        collateral_vault_peripheral.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(collateral_vault_peripheral, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        collateral_vault_peripheral.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(collateral_vault_peripheral, contract_owner, borrower):
    collateral_vault_peripheral.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral, name="OwnerProposed")

    assert collateral_vault_peripheral.owner() == contract_owner
    assert collateral_vault_peripheral.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(collateral_vault_peripheral, contract_owner, borrower):
    collateral_vault_peripheral.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        collateral_vault_peripheral.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(collateral_vault_peripheral, contract_owner, borrower):
    collateral_vault_peripheral.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        collateral_vault_peripheral.claimOwnership(sender=contract_owner)


def test_claim_ownership(collateral_vault_peripheral, contract_owner, borrower):
    collateral_vault_peripheral.proposeOwner(borrower, sender=contract_owner)

    collateral_vault_peripheral.claimOwnership(sender=borrower)
    event = get_last_event(collateral_vault_peripheral, name="OwnershipTransferred")

    assert collateral_vault_peripheral.owner() == borrower
    assert collateral_vault_peripheral.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_add_loans_peripheral_address_wrong_sender(collateral_vault_peripheral, borrower):
    erc20 = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral.addLoansPeripheralAddress(erc20, ZERO_ADDRESS, sender=borrower)


def test_add_loans_peripheral_address_zero_address(collateral_vault_peripheral, contract_owner):
    erc20 = boa.env.generate_address()
    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral.addLoansPeripheralAddress(erc20, ZERO_ADDRESS, sender=contract_owner)


def test_add_loans_peripheral_address(collateral_vault_peripheral, contract_owner):
    erc20 = boa.env.generate_address()
    loans_peripheral = boa.env.generate_address()

    collateral_vault_peripheral.addLoansPeripheralAddress(erc20, loans_peripheral, sender=contract_owner)

    event = get_last_event(collateral_vault_peripheral, name="LoansPeripheralAddressAdded")
    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_peripheral
    assert event.erc20TokenContract == erc20

    assert collateral_vault_peripheral.loansPeripheralAddresses(erc20) == loans_peripheral


def test_add_loans_peripheral_address_same_address(collateral_vault_peripheral, contract_owner):
    erc20 = boa.env.generate_address()
    loans_peripheral = boa.env.generate_address()

    collateral_vault_peripheral.addLoansPeripheralAddress(erc20, loans_peripheral, sender=contract_owner)
    assert collateral_vault_peripheral.loansPeripheralAddresses(erc20) == loans_peripheral

    with boa.reverts("new value is the same"):
        collateral_vault_peripheral.addLoansPeripheralAddress(erc20, loans_peripheral, sender=contract_owner)


def test_remove_loans_peripheral_address_wrong_sender(collateral_vault_peripheral, borrower):
    erc20 = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral.removeLoansPeripheralAddress(erc20, sender=borrower)


def test_remove_loans_peripheral_address_zero_address(collateral_vault_peripheral, contract_owner):
    with boa.reverts("erc20TokenAddr is the zero addr"):
        collateral_vault_peripheral.removeLoansPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_remove_loans_peripheral_address_not_found(collateral_vault_peripheral, contract_owner):
    erc20 = boa.env.generate_address()
    with boa.reverts("address not found"):
        collateral_vault_peripheral.removeLoansPeripheralAddress(erc20, sender=contract_owner)


def test_remove_loans_peripheral_address(collateral_vault_peripheral, contract_owner):
    erc20 = boa.env.generate_address()
    loans_peripheral = boa.env.generate_address()

    collateral_vault_peripheral.addLoansPeripheralAddress(erc20, loans_peripheral, sender=contract_owner)

    assert collateral_vault_peripheral.loansPeripheralAddresses(erc20) == loans_peripheral

    collateral_vault_peripheral.removeLoansPeripheralAddress(erc20, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral, name="LoansPeripheralAddressRemoved")

    assert collateral_vault_peripheral.loansPeripheralAddresses(erc20) == ZERO_ADDRESS

    assert event.currentValue == loans_peripheral
    assert event.erc20TokenContract == erc20


def test_set_collateral_vault_peripheral_address_wrong_sender(collateral_vault_peripheral, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=borrower)


def test_set_collateral_vault_peripheral_address_zero_address(collateral_vault_peripheral, contract_owner):
    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_peripheral_address(collateral_vault_peripheral, contract_owner):
    liquidations_peripheral = boa.env.generate_address()
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral, name="LiquidationsPeripheralAddressSet")

    assert collateral_vault_peripheral.liquidationsPeripheralAddress() == liquidations_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == liquidations_peripheral


def test_set_collateral_vault_peripheral_address_same_address(collateral_vault_peripheral, contract_owner):
    liquidations_peripheral = boa.env.generate_address()
    collateral_vault_peripheral.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    assert collateral_vault_peripheral.liquidationsPeripheralAddress() == liquidations_peripheral

    with boa.reverts("new value is the same"):
        collateral_vault_peripheral.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)


def test_transfer_collateral_from_loan_mapping_not_found(collateral_vault_peripheral, borrower):
    erc20 = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    with boa.reverts("mapping not found"):
        collateral_vault_peripheral.transferCollateralFromLoan(borrower, erc721, 0, erc20)


def test_store_collateral_mapping_not_found(collateral_vault_peripheral, borrower):
    erc20 = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    with boa.reverts("mapping not found"):
        collateral_vault_peripheral.storeCollateral(borrower, erc721, 0, erc20, False)
