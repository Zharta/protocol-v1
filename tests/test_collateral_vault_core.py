import brownie
import pytest


@pytest.fixture
def contract_owner(accounts):
    yield accounts[0]


@pytest.fixture
def borrower(accounts):
    yield accounts[1]


@pytest.fixture
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {"from": contract_owner})


@pytest.fixture
def erc721_contract(ERC721, contract_owner):
    yield ERC721.deploy({'from': contract_owner})


@pytest.fixture
def collateral_vault_core_contract(CollateralVaultCore, contract_owner):
    yield CollateralVaultCore.deploy(
        {"from": contract_owner}
    )


@pytest.fixture
def collateral_vault_peripheral_contract(CollateralVaultPeripheral, collateral_vault_core_contract, contract_owner):
    yield CollateralVaultPeripheral.deploy(
        collateral_vault_core_contract,
        {"from": contract_owner}
    )


def test_initial_state(collateral_vault_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(collateral_vault_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        collateral_vault_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(collateral_vault_core_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        collateral_vault_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(collateral_vault_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        collateral_vault_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(collateral_vault_core_contract, contract_owner, borrower):
    tx = collateral_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert collateral_vault_core_contract.owner() == contract_owner
    assert collateral_vault_core_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(collateral_vault_core_contract, contract_owner, borrower):
    collateral_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        collateral_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(collateral_vault_core_contract, contract_owner, borrower):
    collateral_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        collateral_vault_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(collateral_vault_core_contract, contract_owner, borrower):
    collateral_vault_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = collateral_vault_core_contract.claimOwnership({"from": borrower})

    assert collateral_vault_core_contract.owner() == borrower
    assert collateral_vault_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_collateral_vault_peripheral_address_wrong_sender(collateral_vault_core_contract, collateral_vault_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": borrower})


def test_set_collateral_vault_address_peripheral_zero_address(collateral_vault_core_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_collateral_vault_peripheral_address(collateral_vault_core_contract, collateral_vault_peripheral_contract, contract_owner):
    tx = collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_core_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    event = tx.events["CollateralVaultPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == collateral_vault_peripheral_contract


def test_set_collateral_vault_address_peripheral_same_address(collateral_vault_core_contract, collateral_vault_peripheral_contract, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_core_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    with brownie.reverts("new value is the same"):
        collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})


def test_store_collateral_wrong_sender(collateral_vault_core_contract, contract_owner):
    with brownie.reverts("msg.sender is not authorised"):
        collateral_vault_core_contract.storeCollateral(contract_owner, brownie.ZERO_ADDRESS, 0, {"from": contract_owner})


def test_store_collateral(collateral_vault_core_contract, collateral_vault_peripheral_contract, erc721_contract, borrower, contract_owner):
    erc721_contract.mint(borrower, 0, {"from": contract_owner})
    erc721_contract.approve(collateral_vault_core_contract, 0, {"from": borrower})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.storeCollateral(borrower, erc721_contract, 0, {"from": collateral_vault_peripheral_contract})

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract


def test_transfer_collateral_wrong_sender(collateral_vault_core_contract, contract_owner):
    with brownie.reverts("msg.sender is not authorised"):
        collateral_vault_core_contract.transferCollateral(contract_owner, brownie.ZERO_ADDRESS, 0, {"from": contract_owner})


def test_transfer_collateral(collateral_vault_core_contract, collateral_vault_peripheral_contract, erc721_contract, borrower, contract_owner):
    erc721_contract.mint(borrower, 0, {"from": contract_owner})
    erc721_contract.approve(collateral_vault_core_contract, 0, {"from": borrower})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.storeCollateral(borrower, erc721_contract, 0, {"from": collateral_vault_peripheral_contract})

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract

    collateral_vault_core_contract.transferCollateral(borrower, erc721_contract, 0, {"from": collateral_vault_peripheral_contract})

    assert erc721_contract.ownerOf(0) == borrower
