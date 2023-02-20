import boa
import os
import pytest
from web3 import Web3

from ..conftest import ZERO_ADDRESS, get_last_event

def test_initial_state(collateral_vault_peripheral_contract, collateral_vault_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_peripheral_contract.owner() == contract_owner
    assert collateral_vault_peripheral_contract.collateralVaultCoreDefaultAddress() == collateral_vault_core_contract.address


def test_propose_owner_wrong_sender(collateral_vault_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(collateral_vault_peripheral_contract, contract_owner):
    with boa.reverts("address it the zero address"):
        collateral_vault_peripheral_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(collateral_vault_peripheral_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        collateral_vault_peripheral_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral_contract, name="OwnerProposed")

    assert collateral_vault_peripheral_contract.owner() == contract_owner
    assert collateral_vault_peripheral_contract.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, sender=contract_owner)
    
    with boa.reverts("proposed owner addr is the same"):
        collateral_vault_peripheral_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        collateral_vault_peripheral_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    tx = collateral_vault_peripheral_contract.claimOwnership(sender=borrower)
    event = get_last_event(collateral_vault_peripheral_contract, name="OwnershipTransferred")

    assert collateral_vault_peripheral_contract.owner() == borrower
    assert collateral_vault_peripheral_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_add_loans_peripheral_address_wrong_sender(collateral_vault_peripheral_contract, erc20_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, ZERO_ADDRESS, sender=borrower)


def test_add_loans_peripheral_address_zero_address(collateral_vault_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, ZERO_ADDRESS, sender=contract_owner)


def test_add_loans_peripheral_address_not_contract(collateral_vault_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, contract_owner, sender=contract_owner)


def test_add_loans_peripheral_address(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, loans_peripheral_contract, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral_contract, name="LoansPeripheralAddressAdded")

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract.address) == loans_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_peripheral_contract.address
    assert event.erc20TokenContract == erc20_contract.address


def test_add_loans_peripheral_address_same_address(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, loans_peripheral_contract, sender=contract_owner)

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract.address) == loans_peripheral_contract.address

    with boa.reverts("new value is the same"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, loans_peripheral_contract, sender=contract_owner)


def test_remove_loans_peripheral_address_wrong_sender(collateral_vault_peripheral_contract, erc20_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(erc20_contract.address, sender=borrower)


def test_remove_loans_peripheral_address_zero_address(collateral_vault_peripheral_contract, contract_owner):
    with boa.reverts("erc20TokenAddr is the zero addr"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_remove_loans_peripheral_address_not_contract(collateral_vault_peripheral_contract, contract_owner):
    with boa.reverts("erc20TokenAddr is not a contract"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(contract_owner, sender=contract_owner)


def test_remove_loans_peripheral_address_not_found(collateral_vault_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address not found"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(erc20_contract.address, sender=contract_owner)


def test_remove_loans_peripheral_address(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract.address, loans_peripheral_contract, sender=contract_owner)

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract.address) == loans_peripheral_contract.address

    collateral_vault_peripheral_contract.removeLoansPeripheralAddress(erc20_contract.address, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral_contract, name="LoansPeripheralAddressRemoved")

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract.address) == ZERO_ADDRESS

    assert event.currentValue == loans_peripheral_contract.address
    assert event.erc20TokenContract == erc20_contract.address


def test_set_collateral_vault_peripheral_address_wrong_sender(collateral_vault_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=borrower)


def test_set_collateral_vault_peripheral_address_zero_address(collateral_vault_peripheral_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_peripheral_address_not_contract(collateral_vault_peripheral_contract, contract_owner):
    with boa.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(contract_owner, sender=contract_owner)


def test_set_collateral_vault_peripheral_address(collateral_vault_peripheral_contract, liquidations_peripheral_contract, contract_owner):
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
    event = get_last_event(collateral_vault_peripheral_contract, name="LiquidationsPeripheralAddressSet")

    assert collateral_vault_peripheral_contract.liquidationsPeripheralAddress() == liquidations_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == liquidations_peripheral_contract.address


def test_set_collateral_vault_peripheral_address_same_address(collateral_vault_peripheral_contract, liquidations_peripheral_contract, contract_owner):
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)

    assert collateral_vault_peripheral_contract.liquidationsPeripheralAddress() == liquidations_peripheral_contract.address

    with boa.reverts("new value is the same"):
        collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)


def test_store_collateral_zero_values(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.storeCollateral(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS
        )

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS
        )

    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            ZERO_ADDRESS
        )


def test_store_collateral_not_contracts(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with boa.reverts("collat addr is not a contract"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            borrower,
            0,
            borrower
        )

    with boa.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            borrower
        )


def test_store_collateral_mapping_not_found(collateral_vault_peripheral_contract, erc721_contract, erc20_contract, borrower):
    with boa.reverts("mapping not found"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_store_collateral_wrong_sender(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
    
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_store_collateral_not_nft_contract(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    with boa.reverts():
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc20_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_store_collateral_wrong_owner(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by wallet"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_store_collateral_not_approved(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(borrower, 0, sender=contract_owner)

    with boa.reverts("transfer is not approved"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_store_collateral(collateral_vault_peripheral_contract, collateral_vault_core_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_core_contract, 0, sender=borrower)

    tx = collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_peripheral_contract, name="CollateralStored")

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract.address

    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event._from == borrower


def test_store_cryptopunk_collateral(
    collateral_vault_peripheral_contract,
    cryptopunks_vault_core_contract,
    loans_peripheral_contract,
    cryptopunks_market_contract,
    cryptopunk_collaterals,
    erc20_contract,
    borrower,
    contract_owner
):
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract)
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, sender=borrower)

    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_peripheral_contract, name="CollateralStored")

    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract.address

    assert event.collateralAddress == cryptopunks_market_contract.address
    assert event.tokenId == 0
    assert event._from == borrower

    cryptopunks_market_contract.transferPunk(borrower, 0, sender=cryptopunks_vault_core_contract.address)


def test_transfer_collateral_from_loan_zero_values(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS
        )

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS
        )

    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            ZERO_ADDRESS
        )


def test_transfer_collateral_from_loan_not_contracts(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with boa.reverts("collat addr is not a contract"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            borrower,
            0,
            borrower
        )

    with boa.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            borrower
        )


def test_transfer_collateral_from_loan_mapping_not_found(collateral_vault_peripheral_contract, erc721_contract, erc20_contract, borrower):
    with boa.reverts("mapping not found"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_transfer_collateral_from_loan_wrong_sender(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
    
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_transfer_collateral_from_loan_not_nft_contract(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    with boa.reverts():
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc20_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_transfer_collateral_from_loan_wrong_owner(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by CVCore"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_transfer_collateral_from_loan(collateral_vault_peripheral_contract, collateral_vault_core_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_core_contract, 0, sender=borrower)


    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract.address

    collateral_vault_peripheral_contract.transferCollateralFromLoan(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_peripheral_contract, name="CollateralFromLoanTransferred")

    assert erc721_contract.ownerOf(0) == borrower

    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_cryptopunk_collateral_from_loan(
    collateral_vault_peripheral_contract,
    cryptopunks_vault_core_contract,
    loans_peripheral_contract,
    cryptopunks_market_contract,
    cryptopunk_collaterals,
    erc20_contract,
    borrower,
    contract_owner
):
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract, sender=contract_owner)
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, sender=borrower)


    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )

    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract.address

    collateral_vault_peripheral_contract.transferCollateralFromLoan(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_peripheral_contract, name="CollateralFromLoanTransferred")

    assert cryptopunks_market_contract.punkIndexToAddress(0) == borrower

    assert event.collateralAddress == cryptopunks_market_contract.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_collateral_from_liquidation_wrong_sender(collateral_vault_peripheral_contract):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0
        )


def test_transfer_collateral_from_liquidation_zero_values(collateral_vault_peripheral_contract, liquidations_peripheral_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)

    with boa.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0,
            sender=liquidations_peripheral_contract.address
        )

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            ZERO_ADDRESS,
            0,
            sender=liquidations_peripheral_contract.address
        )


def test_transfer_collateral_from_liquidation_not_contract(collateral_vault_peripheral_contract, liquidations_peripheral_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)

    with boa.reverts("collat addr is not a contract"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            borrower,
            0,
            sender=liquidations_peripheral_contract.address
        )


def test_transfer_collateral_from_liquidation_not_nft_contract(collateral_vault_peripheral_contract, liquidations_peripheral_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)

    with boa.reverts():
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            erc20_contract,
            0,
            sender=liquidations_peripheral_contract.address
        )


def test_transfer_collateral_from_liquidation_wrong_owner(collateral_vault_peripheral_contract, liquidations_peripheral_contract, erc721_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by CVCore"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            erc721_contract,
            0,
            sender=liquidations_peripheral_contract.address
        )


def test_transfer_collateral_from_liquidation(collateral_vault_peripheral_contract, collateral_vault_core_contract, loans_peripheral_contract, liquidations_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)

    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)

    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_core_contract, 0, sender=borrower)

 
    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract.address

    collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
        borrower,
        erc721_contract,
        0,
        sender=liquidations_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_peripheral_contract, name="CollateralFromLiquidationTransferred")

    assert erc721_contract.ownerOf(0) == borrower

    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_collateral_from_liquidation(
    collateral_vault_peripheral_contract,
    cryptopunks_vault_core_contract,
    loans_peripheral_contract,
    liquidations_peripheral_contract,
    cryptopunks_market_contract,
    cryptopunk_collaterals,
    erc20_contract,
    borrower,
    contract_owner
):
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=contract_owner)
    collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract)
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core_contract, sender=borrower)

    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )

    assert cryptopunks_market_contract.punkIndexToAddress(0) == cryptopunks_vault_core_contract.address

    collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
        borrower,
        cryptopunks_market_contract,
        0,
        sender=liquidations_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_peripheral_contract, name="CollateralFromLiquidationTransferred")

    assert cryptopunks_market_contract.punkIndexToAddress(0) == borrower

    assert event.collateralAddress == cryptopunks_market_contract.address
    assert event.tokenId == 0
    assert event._to == borrower
