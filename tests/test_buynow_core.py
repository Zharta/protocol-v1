from brownie.network import chain
from web3 import Web3

import brownie
import pytest


GRACE_PERIOD_DURATION = 172800 # 2 days
BUY_NOW_PERIOD_DURATION = 604800 # 15 days
AUCTION_DURATION = 604800 # 15 days

PRINCIPAL = Web3.toWei(1, "ether")
INTEREST_AMOUNT = Web3.toWei(0.1, "ether")
APR = 200



@pytest.fixture
def contract_owner(accounts):
    yield accounts[0]


@pytest.fixture
def borrower(accounts):
    yield accounts[1]


@pytest.fixture
def collateral_vault_contract(accounts):
    yield accounts[2]


@pytest.fixture
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("Wrapped Ether", "WETH", 18, 0, {"from": contract_owner})


@pytest.fixture
def erc721_contract(ERC721, contract_owner):
    yield ERC721.deploy({'from': contract_owner})


@pytest.fixture
def loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


@pytest.fixture
def buy_now_peripheral_contract(BuyNowPeripheral, contract_owner):
    yield BuyNowPeripheral.deploy(
        GRACE_PERIOD_DURATION,
        BUY_NOW_PERIOD_DURATION,
        AUCTION_DURATION,
        {"from": contract_owner}
    )


@pytest.fixture
def buy_now_core_contract(BuyNowCore, contract_owner):
    yield BuyNowCore.deploy({"from": contract_owner})


def test_initial_state(buy_now_core_contract, contract_owner,):
    # Check if the constructor of the contract is set up properly
    assert buy_now_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(buy_now_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(buy_now_core_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        buy_now_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(buy_now_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        buy_now_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(buy_now_core_contract, contract_owner, borrower):
    tx = buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert buy_now_core_contract.owner() == contract_owner
    assert buy_now_core_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(buy_now_core_contract, contract_owner, borrower):
    buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(buy_now_core_contract, contract_owner, borrower):
    buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        buy_now_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(buy_now_core_contract, contract_owner, borrower):
    buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = buy_now_core_contract.claimOwnership({"from": borrower})

    assert buy_now_core_contract.owner() == borrower
    assert buy_now_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_collateral_vault_address_wrong_sender(buy_now_core_contract, collateral_vault_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": borrower})


def test_set_collateral_vault_address_zero_address(buy_now_core_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_core_contract.setCollateralVaultAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_collateral_vault_address(buy_now_core_contract, collateral_vault_contract, contract_owner):
    tx = buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    assert buy_now_core_contract.collateralVaultAddress() == collateral_vault_contract

    event = tx.events["CollateralVaultAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == collateral_vault_contract


def test_set_collateral_vault_address_same_address(buy_now_core_contract, collateral_vault_contract, contract_owner):
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    assert buy_now_core_contract.collateralVaultAddress() == collateral_vault_contract

    with brownie.reverts("new value is the same"):
        buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})


def test_set_buy_now_peripheral_address_wrong_sender(buy_now_core_contract, buy_now_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": borrower})


def test_set_buy_now_peripheral_address_zero_address(buy_now_core_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_core_contract.setBuyNowPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_buy_now_peripheral_address_not_contract(buy_now_core_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_core_contract.setBuyNowPeripheralAddress(contract_owner, {"from": contract_owner})


def test_set_buy_now_peripheral_address(buy_now_core_contract, buy_now_peripheral_contract, contract_owner):
    tx = buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    assert buy_now_core_contract.buyNowPeripheralAddress() == buy_now_peripheral_contract

    event = tx.events["BuyNowPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == buy_now_peripheral_contract


def test_set_buy_now_peripheral_address_same_address(buy_now_core_contract, buy_now_peripheral_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    assert buy_now_core_contract.buyNowPeripheralAddress() == buy_now_peripheral_contract

    with brownie.reverts("new value is the same"):
        buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})


def test_add_loans_core_address_wrong_sender(buy_now_core_contract, loans_core_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": borrower})


def test_add_loans_core_address_zero_address(buy_now_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_loans_core_address_not_contract(buy_now_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_loans_core_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    tx = buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    event = tx.events["LoansCoreAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_loans_core_address_same_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    with brownie.reverts("new value is the same"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})


def test_remove_loans_core_address_wrong_sender(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.removeLoansCoreAddress(erc20_contract, {"from": borrower})


def test_remove_loans_core_address_zero_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    with brownie.reverts("erc20TokenAddr is the zero addr"):
        buy_now_core_contract.removeLoansCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_loans_core_address_not_found(buy_now_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        buy_now_core_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})


def test_remove_loans_core_address_zero_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    tx = buy_now_core_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LoansCoreAddressRemoved"]
    assert event["currentValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_liquidation_wrong_sender(buy_now_core_contract, borrower):
    with brownie.reverts("msg.sender is not BNPeriph addr"):
        buy_now_core_contract.addLiquidation(
            brownie.ZERO_ADDRESS,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": borrower}
        )


def test_add_liquidation_collateral_zero_address(buy_now_core_contract, buy_now_peripheral_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("collat addr is the zero address"):
        buy_now_core_contract.addLiquidation(
            brownie.ZERO_ADDRESS,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )


def test_add_liquidation_collateral_not_contract(buy_now_core_contract, buy_now_peripheral_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("collat addr is not a contract"):
        buy_now_core_contract.addLiquidation(
            contract_owner,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )


def test_add_liquidation_collateral_not_erc721(buy_now_core_contract, buy_now_peripheral_contract, erc20_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts(""):
        buy_now_core_contract.addLiquidation(
            erc20_contract,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )


def test_add_liquidation_collateral_not_owned_by_vault(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_contract, erc721_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by vault"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )




def test_add_liquidation_collateral_zero_values(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_contract, erc721_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    with brownie.reverts("startTime is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )
    
    with brownie.reverts("gpmaturity is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )

    with brownie.reverts("bnpmaturity is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )
    
    with brownie.reverts("principal is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )

    with brownie.reverts("interestAmount is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )
    
    with brownie.reverts("apr is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )
    
    with brownie.reverts("apr is 0"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )
    
    with brownie.reverts("borrower is the zero addr"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )

    with brownie.reverts("erc20TokenAddr is the zero addr"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            brownie.ZERO_ADDRESS,
            {"from": buy_now_peripheral_contract}
        )


def test_add_liquidation_erc20_not_a_contract(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_contract, erc721_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    with brownie.reverts("erc20TokenAddr is not a contract"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            chain.time(),
            chain.time() + GRACE_PERIOD_DURATION,
            chain.time() + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            borrower,
            {"from": buy_now_peripheral_contract}
        )


def test_add_liquidation(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    tx = buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            start_time,
            start_time + GRACE_PERIOD_DURATION,
            start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            erc20_contract,
            {"from": buy_now_peripheral_contract}
    )

    liquidation = buy_now_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["startTime"] == start_time
    assert liquidation["gracePeriodMaturity"] == start_time + GRACE_PERIOD_DURATION
    assert liquidation["buyNowPeriodMaturity"] == start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION
    assert liquidation["principal"] == PRINCIPAL
    assert liquidation["interestAmount"] == INTEREST_AMOUNT
    assert liquidation["apr"] == APR
    assert liquidation["borrower"] == borrower
    assert liquidation["erc20TokenContract"] == erc20_contract

    event = tx.events["LiquidationAdded"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["erc20TokenContract"] == erc20_contract


def test_add_liquidation_already_exists(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            start_time,
            start_time + GRACE_PERIOD_DURATION,
            start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            erc20_contract,
            {"from": buy_now_peripheral_contract}
    )

    with brownie.reverts("liquidation already exists"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            start_time,
            start_time + GRACE_PERIOD_DURATION,
            start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            erc20_contract,
            {"from": buy_now_peripheral_contract}
        )


def test_remove_liquidation_wrong_sender(buy_now_core_contract, erc721_contract, contract_owner):
    with brownie.reverts("msg.sender is not BNPeriph addr"):
        buy_now_core_contract.removeLiquidation(erc721_contract, 0, {"from": contract_owner})


def test_remove_liquidation_not_found(buy_now_core_contract, buy_now_peripheral_contract, erc721_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("liquidation not found"):
        buy_now_core_contract.removeLiquidation(erc721_contract, 0, {"from": buy_now_peripheral_contract})


def test_remove_liquidation_(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            start_time,
            start_time + GRACE_PERIOD_DURATION,
            start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            erc20_contract,
            {"from": buy_now_peripheral_contract}
    )
    
    tx = buy_now_core_contract.removeLiquidation(erc721_contract, 0, {"from": buy_now_peripheral_contract})

    liquidation = buy_now_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

    event = tx.events["LiquidationRemoved"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["erc20TokenContract"] == erc20_contract





