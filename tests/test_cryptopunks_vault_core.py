import brownie
import pytest
import os


def test_initial_state(cryptopunks_vault_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert cryptopunks_vault_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(cryptopunks_vault_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        cryptopunks_vault_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(cryptopunks_vault_core_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        cryptopunks_vault_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(cryptopunks_vault_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        cryptopunks_vault_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(cryptopunks_vault_core_contract, contract_owner, borrower):
    tx = cryptopunks_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert cryptopunks_vault_core_contract.owner() == contract_owner
    assert cryptopunks_vault_core_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})
    with brownie.reverts("proposed owner addr is the same"):
        cryptopunks_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        cryptopunks_vault_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(cryptopunks_vault_core_contract, contract_owner, borrower):
    cryptopunks_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = cryptopunks_vault_core_contract.claimOwnership({"from": borrower})

    assert cryptopunks_vault_core_contract.owner() == borrower
    assert cryptopunks_vault_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_collateral_vault_peripheral_address_wrong_sender(cryptopunks_vault_core_contract, collateral_vault_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": borrower})


def test_set_collateral_vault_address_peripheral_zero_address(cryptopunks_vault_core_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_collateral_vault_peripheral_address(cryptopunks_vault_core_contract, collateral_vault_peripheral_contract, contract_owner):
    tx = cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert cryptopunks_vault_core_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    event = tx.events["CollateralVaultPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == collateral_vault_peripheral_contract


def test_store_collateral_wrong_sender(cryptopunks_vault_core_contract, contract_owner):
    with brownie.reverts("msg.sender is not authorised"):
        cryptopunks_vault_core_contract.storeCollateral(contract_owner, brownie.ZERO_ADDRESS, 0, {"from": contract_owner})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_store_collateral_invalid_contract(cryptopunks_vault_core_contract, collateral_vault_peripheral_contract, erc721_contract, borrower, contract_owner):
    erc721_contract.mint(borrower, 0, {"from": contract_owner})
    erc721_contract.approve(cryptopunks_vault_core_contract, 0, {"from": borrower})

    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("address not supported by vault"):
        cryptopunks_vault_core_contract.storeCollateral(contract_owner, brownie.ZERO_ADDRESS, 0, {"from": collateral_vault_peripheral_contract})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_store_collateral(
    cryptopunks_vault_core_contract,
    collateral_vault_peripheral_contract,
    cryptopunk_collaterals,
    cryptopunks_market_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, {"from": borrower})
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    cryptopunks_vault_core_contract.storeCollateral(borrower, cryptopunks_market_contract, 0, {"from": collateral_vault_peripheral_contract})

    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract
    cryptopunks_market_contract.transferPunk(borrower, 0, {'from': cryptopunks_vault_core_contract})


def test_transfer_collateral_wrong_sender(cryptopunks_vault_core_contract, contract_owner):
    with brownie.reverts("msg.sender is not authorised"):
        cryptopunks_vault_core_contract.transferCollateral(contract_owner, brownie.ZERO_ADDRESS, 0, {"from": contract_owner})


@pytest.mark.require_network("ganache-mainnet-fork")
def test_transfer_collateral(
    cryptopunks_vault_core_contract,
    collateral_vault_peripheral_contract,
    cryptopunk_collaterals,
    cryptopunks_market_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, {"from": borrower})
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    cryptopunks_vault_core_contract.storeCollateral(borrower, cryptopunks_market_contract, 0, {"from": collateral_vault_peripheral_contract})
    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract

    cryptopunks_vault_core_contract.transferCollateral(borrower, cryptopunks_market_contract, 0, {"from": collateral_vault_peripheral_contract})
    assert cryptopunks_market_contract.punkIndexToAddress(0) == borrower
