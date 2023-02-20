import boa
import pytest

from ..conftest import ZERO_ADDRESS, get_last_event


def test_initial_state(cryptopunks_vault_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert cryptopunks_vault_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(cryptopunks_vault_core_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        cryptopunks_vault_core_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(cryptopunks_vault_core_contract, contract_owner):
    with boa.reverts("address it the zero address"):
        cryptopunks_vault_core_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(cryptopunks_vault_core_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        cryptopunks_vault_core_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(cryptopunks_vault_core_contract, name="OwnerProposed")

    assert cryptopunks_vault_core_contract.owner() == contract_owner
    assert cryptopunks_vault_core_contract.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, sender=contract_owner)
    with boa.reverts("proposed owner addr is the same"):
        cryptopunks_vault_core_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        cryptopunks_vault_core_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, sender=contract_owner)

    cryptopunks_vault_core_contract.claimOwnership(sender=borrower)
    event = get_last_event(cryptopunks_vault_core_contract, name="OwnershipTransferred")

    assert cryptopunks_vault_core_contract.owner() == borrower
    assert cryptopunks_vault_core_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_collateral_vault_peripheral_address_wrong_sender(cryptopunks_vault_core_contract, collateral_vault_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=borrower)


def test_set_collateral_vault_address_peripheral_zero_address(cryptopunks_vault_core_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_peripheral_address(cryptopunks_vault_core_contract, collateral_vault_peripheral_contract, contract_owner):
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
    event = get_last_event(cryptopunks_vault_core_contract, name="CollateralVaultPeripheralAddressSet")

    assert cryptopunks_vault_core_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral_contract.address


def test_store_collateral_wrong_sender(cryptopunks_vault_core_contract, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        cryptopunks_vault_core_contract.storeCollateral(contract_owner, ZERO_ADDRESS, 0, sender=contract_owner)


def test_store_collateral_invalid_contract(cryptopunks_vault_core_contract, collateral_vault_peripheral_contract, erc721_contract, borrower, contract_owner):
    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(cryptopunks_vault_core_contract, 0, sender=borrower)

    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    with boa.reverts("address not supported by vault"):
        cryptopunks_vault_core_contract.storeCollateral(contract_owner, ZERO_ADDRESS, 0, sender=collateral_vault_peripheral_contract.address)


def test_store_collateral(
    cryptopunks_vault_core_contract,
    collateral_vault_peripheral_contract,
    cryptopunk_collaterals,
    cryptopunks_market_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, sender=borrower)
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    cryptopunks_vault_core_contract.storeCollateral(borrower, cryptopunks_market_contract, 0, sender=collateral_vault_peripheral_contract.address)

    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract.address
    cryptopunks_market_contract.transferPunk(borrower, 0, sender=cryptopunks_vault_core_contract.address)


def test_transfer_collateral_wrong_sender(cryptopunks_vault_core_contract, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        cryptopunks_vault_core_contract.transferCollateral(contract_owner, ZERO_ADDRESS, 0, sender=contract_owner)


def test_transfer_collateral(
    cryptopunks_vault_core_contract,
    collateral_vault_peripheral_contract,
    cryptopunk_collaterals,
    cryptopunks_market_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, sender=borrower)
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    cryptopunks_vault_core_contract.storeCollateral(borrower, cryptopunks_market_contract, 0, sender=collateral_vault_peripheral_contract.address)
    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract.address

    cryptopunks_vault_core_contract.transferCollateral(borrower, cryptopunks_market_contract, 0, sender=collateral_vault_peripheral_contract.address)
    assert cryptopunks_market_contract.punkIndexToAddress(0) == borrower
