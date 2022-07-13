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
def lending_pool_peripheral_contract(LendingPoolPeripheral, erc20_contract, contract_owner, accounts):
    yield LendingPoolPeripheral.deploy(
        accounts[3],
        erc20_contract,
        accounts[4],
        1000,
        7000,
        False,
        {'from': contract_owner}
    )


@pytest.fixture
def loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


@pytest.fixture
def loans_peripheral_contract(Loans, loans_core_contract, lending_pool_peripheral_contract, contract_owner, accounts):
    yield Loans.deploy(
        1,
        1,
        0,
        1,
        loans_core_contract,
        lending_pool_peripheral_contract,
        accounts[5],
        {'from': contract_owner}
    )



@pytest.fixture
def buy_now_core_contract(BuyNowCore, contract_owner):
    yield BuyNowCore.deploy({"from": contract_owner})


@pytest.fixture
def buy_now_peripheral_contract(BuyNowPeripheral, buy_now_core_contract, contract_owner):
    yield BuyNowPeripheral.deploy(
        buy_now_core_contract,
        10000,
        10000,
        10000,
        {"from": contract_owner}
    )


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


def test_initial_state(collateral_vault_peripheral_contract, collateral_vault_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_peripheral_contract.owner() == contract_owner
    assert collateral_vault_peripheral_contract.collateralVaultCoreAddress() == collateral_vault_core_contract


def test_propose_owner_wrong_sender(collateral_vault_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(collateral_vault_peripheral_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        collateral_vault_peripheral_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(collateral_vault_peripheral_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        collateral_vault_peripheral_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(collateral_vault_peripheral_contract, contract_owner, borrower):
    tx = collateral_vault_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.owner() == contract_owner
    assert collateral_vault_peripheral_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        collateral_vault_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        collateral_vault_peripheral_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(collateral_vault_peripheral_contract, contract_owner, borrower):
    collateral_vault_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = collateral_vault_peripheral_contract.claimOwnership({"from": borrower})

    assert collateral_vault_peripheral_contract.owner() == borrower
    assert collateral_vault_peripheral_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_add_loans_peripheral_address_wrong_sender(collateral_vault_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": borrower})


def test_add_loans_peripheral_address_zero_address(collateral_vault_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_loans_peripheral_address_not_contract(collateral_vault_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_loans_peripheral_address(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, contract_owner):
    tx = collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract) == loans_peripheral_contract

    event = tx.events["LoansPeripheralAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_peripheral_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_loans_peripheral_address_same_address(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract) == loans_peripheral_contract

    with brownie.reverts("new value is the same"):
        collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})


def test_remove_loans_peripheral_address_wrong_sender(collateral_vault_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(erc20_contract, {"from": borrower})


def test_remove_loans_peripheral_address_zero_address(collateral_vault_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_loans_peripheral_address_not_contract(collateral_vault_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(contract_owner, {"from": contract_owner})


def test_remove_loans_peripheral_address_not_found(collateral_vault_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        collateral_vault_peripheral_contract.removeLoansPeripheralAddress(erc20_contract, {"from": contract_owner})


def test_remove_loans_peripheral_address(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract) == loans_peripheral_contract

    tx = collateral_vault_peripheral_contract.removeLoansPeripheralAddress(erc20_contract, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.loansPeripheralAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LoansPeripheralAddressRemoved"]
    assert event["currentValue"] == loans_peripheral_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_set_buy_now_peripheral_address_wrong_sender(collateral_vault_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(brownie.ZERO_ADDRESS, {"from": borrower})


def test_set_buy_now_peripheral_address_zero_address(collateral_vault_peripheral_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_buy_now_peripheral_address_not_contract(collateral_vault_peripheral_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(contract_owner, {"from": contract_owner})


def test_set_buy_now_peripheral_address(collateral_vault_peripheral_contract, buy_now_peripheral_contract, contract_owner):
    tx = collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.buyNowPeripheralAddress() == buy_now_peripheral_contract

    event = tx.events["BuyNowPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == buy_now_peripheral_contract


def test_set_buy_now_peripheral_address_same_address(collateral_vault_peripheral_contract, buy_now_peripheral_contract, contract_owner):
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    assert collateral_vault_peripheral_contract.buyNowPeripheralAddress() == buy_now_peripheral_contract

    with brownie.reverts("new value is the same"):
        collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})


def test_store_collateral_zero_values(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.storeCollateral(
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )

    with brownie.reverts("collat addr is the zero addr"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )

    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            brownie.ZERO_ADDRESS
        )


def test_store_collateral_not_contracts(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with brownie.reverts("collat addr is not a contract"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            borrower,
            0,
            borrower
        )

    with brownie.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            borrower
        )


def test_store_collateral_mapping_not_found(collateral_vault_peripheral_contract, erc721_contract, erc20_contract, borrower):
    with brownie.reverts("mapping not found"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_store_collateral_wrong_sender(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts("msg.sender is not authorised"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_store_collateral_not_nft_contract(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts(""):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc20_contract,
            0,
            erc20_contract,
            {"from": loans_peripheral_contract}
        )


def test_store_collateral_wrong_owner(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by wallet"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            {"from": loans_peripheral_contract}
        )


def test_store_collateral_not_approved(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(borrower, 0, {"from": contract_owner})

    with brownie.reverts("transfer is not approved"):
        collateral_vault_peripheral_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            {"from": loans_peripheral_contract}
        )


def test_store_collateral(collateral_vault_peripheral_contract, collateral_vault_core_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(borrower, 0, {"from": contract_owner})
    erc721_contract.approve(collateral_vault_core_contract, 0, {"from": borrower})

    
    tx = collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        {"from": loans_peripheral_contract}
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract

    event = tx.events["CollateralStored"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["_from"] == borrower


def test_transfer_collateral_from_loan_zero_values(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )

    with brownie.reverts("collat addr is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )

    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            brownie.ZERO_ADDRESS
        )


def test_transfer_collateral_from_loan_not_contracts(collateral_vault_peripheral_contract, erc721_contract, borrower):
    with brownie.reverts("collat addr is not a contract"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            borrower,
            0,
            borrower
        )

    with brownie.reverts("address is not a contract"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            borrower
        )


def test_transfer_collateral_from_loan_mapping_not_found(collateral_vault_peripheral_contract, erc721_contract, erc20_contract, borrower):
    with brownie.reverts("mapping not found"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_transfer_collateral_from_loan_wrong_sender(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts("msg.sender is not authorised"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_transfer_collateral_from_loan_not_nft_contract(collateral_vault_peripheral_contract, loans_peripheral_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts(""):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc20_contract,
            0,
            erc20_contract,
            {"from": loans_peripheral_contract}
        )


def test_transfer_collateral_from_loan_wrong_owner(collateral_vault_peripheral_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by CVCore"):
        collateral_vault_peripheral_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            {"from": loans_peripheral_contract}
        )


def test_transfer_collateral_from_loan(collateral_vault_peripheral_contract, collateral_vault_core_contract, loans_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(borrower, 0, {"from": contract_owner})
    erc721_contract.approve(collateral_vault_core_contract, 0, {"from": borrower})

    
    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        {"from": loans_peripheral_contract}
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract

    tx = collateral_vault_peripheral_contract.transferCollateralFromLoan(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        {"from": loans_peripheral_contract}
    )

    assert erc721_contract.ownerOf(0) == borrower

    event = tx.events["CollateralFromLoanTransferred"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["_to"] == borrower


def test_transfer_collateral_from_liquidation_wrong_sender(collateral_vault_peripheral_contract):
    with brownie.reverts("msg.sender is not authorised"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            0
        )


def test_transfer_collateral_from_liquidation_zero_values(collateral_vault_peripheral_contract, buy_now_peripheral_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("address is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            0,
            {"from": buy_now_peripheral_contract}
        )

    with brownie.reverts("collat addr is the zero addr"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            brownie.ZERO_ADDRESS,
            0,
            {"from": buy_now_peripheral_contract}
        )


def test_transfer_collateral_from_liquidation_not_contract(collateral_vault_peripheral_contract, buy_now_peripheral_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("collat addr is not a contract"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            borrower,
            0,
            {"from": buy_now_peripheral_contract}
        )


def test_transfer_collateral_from_liquidation_not_nft_contract(collateral_vault_peripheral_contract, buy_now_peripheral_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts(""):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            erc20_contract,
            0,
            {"from": buy_now_peripheral_contract}
        )


def test_transfer_collateral_from_liquidation_wrong_owner(collateral_vault_peripheral_contract, buy_now_peripheral_contract, erc721_contract, borrower, contract_owner):
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by CVCore"):
        collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
            borrower,
            erc721_contract,
            0,
            {"from": buy_now_peripheral_contract}
        )


def test_transfer_collateral_from_liquidation(collateral_vault_peripheral_contract, collateral_vault_core_contract, loans_peripheral_contract, buy_now_peripheral_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(borrower, 0, {"from": contract_owner})
    erc721_contract.approve(collateral_vault_core_contract, 0, {"from": borrower})

    
    collateral_vault_peripheral_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        {"from": loans_peripheral_contract}
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_core_contract

    tx = collateral_vault_peripheral_contract.transferCollateralFromLiquidation(
        borrower,
        erc721_contract,
        0,
        {"from": buy_now_peripheral_contract}
    )

    assert erc721_contract.ownerOf(0) == borrower

    event = tx.events["CollateralFromLiquidationTransferred"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["_to"] == borrower
