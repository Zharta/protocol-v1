import ape
from ape.utils import ZERO_ADDRESS


def test_initial_state(collateral_vault_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(collateral_vault_core_contract, borrower):
    with ape.reverts("msg.sender is not the owner"):
        collateral_vault_core_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(collateral_vault_core_contract, contract_owner):
    with ape.reverts("address it the zero address"):
        collateral_vault_core_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(collateral_vault_core_contract, contract_owner):
    with ape.reverts("proposed owner addr is the owner"):
        collateral_vault_core_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(collateral_vault_core_contract, contract_owner, borrower):
    tx = collateral_vault_core_contract.proposeOwner(borrower, sender=contract_owner)

    assert collateral_vault_core_contract.owner() == contract_owner
    assert collateral_vault_core_contract.proposedOwner() == borrower

    event = tx.events[0]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(collateral_vault_core_contract, contract_owner, borrower):
    collateral_vault_core_contract.proposeOwner(borrower, sender=contract_owner)
    
    with ape.reverts("proposed owner addr is the same"):
        collateral_vault_core_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(collateral_vault_core_contract, contract_owner, borrower):
    collateral_vault_core_contract.proposeOwner(borrower, sender=contract_owner)

    with ape.reverts("msg.sender is not the proposed"):
        collateral_vault_core_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(collateral_vault_core_contract, contract_owner, borrower):
    collateral_vault_core_contract.proposeOwner(borrower, sender=contract_owner)

    tx = collateral_vault_core_contract.claimOwnership(sender=borrower)

    assert collateral_vault_core_contract.owner() == borrower
    assert collateral_vault_core_contract.proposedOwner() == ZERO_ADDRESS

    event = tx.events[0]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_collateral_vault_peripheral_address_wrong_sender(collateral_vault_core_contract, collateral_vault_peripheral_contract, borrower):
    with ape.reverts("msg.sender is not the owner"):
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=borrower)


def test_set_collateral_vault_address_peripheral_zero_address(collateral_vault_core_contract, contract_owner):
    with ape.reverts("address is the zero addr"):
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_peripheral_address(collateral_vault_core_contract, collateral_vault_peripheral_contract, contract_owner):
    tx = collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    assert collateral_vault_core_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    event = tx.events[0]
    assert event["currentValue"] == ZERO_ADDRESS
    assert event["newValue"] == collateral_vault_peripheral_contract


def test_set_collateral_vault_address_peripheral_same_address(collateral_vault_core_contract, collateral_vault_peripheral_contract, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    assert collateral_vault_core_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    with ape.reverts("new value is the same"):
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)


def test_store_collateral_wrong_sender(collateral_vault_core_contract, contract_owner):
    with ape.reverts("msg.sender is not authorised"):
        collateral_vault_core_contract.storeCollateral(contract_owner, ZERO_ADDRESS, 0, sender=contract_owner)


def test_store_collateral(collateral_vault_core_contract, collateral_vault_peripheral_contract, erc721_contract, borrower, contract_owner):
    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_core_contract, 0, sender=borrower)

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    collateral_vault_core_contract.storeCollateral(borrower, erc721_contract, 0, sender=collateral_vault_peripheral_contract)

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract


def test_transfer_collateral_wrong_sender(collateral_vault_core_contract, contract_owner):
    with ape.reverts("msg.sender is not authorised"):
        collateral_vault_core_contract.transferCollateral(contract_owner, ZERO_ADDRESS, 0, sender=contract_owner)


def test_transfer_collateral(collateral_vault_core_contract, collateral_vault_peripheral_contract, erc721_contract, borrower, contract_owner):
    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_core_contract, 0, sender=borrower)

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    collateral_vault_core_contract.storeCollateral(borrower, erc721_contract, 0, sender=collateral_vault_peripheral_contract)

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract

    collateral_vault_core_contract.transferCollateral(borrower, erc721_contract, 0, sender=collateral_vault_peripheral_contract)

    assert erc721_contract.ownerOf(0) == borrower
