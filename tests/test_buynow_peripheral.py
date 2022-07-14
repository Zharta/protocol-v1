from decimal import Decimal
from brownie.network import chain
from datetime import datetime as dt
from web3 import Web3

import brownie
import pytest


GRACE_PERIOD_DURATION = 5
BUY_NOW_PERIOD_DURATION = 5
AUCTION_DURATION = 5

PRINCIPAL = Web3.toWei(1, "ether")
INTEREST_AMOUNT = Web3.toWei(0.1, "ether")
APR = 200

MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


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
def lending_pool_core_contract(LendingPoolCore, erc20_contract, contract_owner):
    yield LendingPoolCore.deploy(
        erc20_contract,
        {'from': contract_owner}
    )


@pytest.fixture
def lending_pool_peripheral_contract(LendingPoolPeripheral, lending_pool_core_contract, erc20_contract, contract_owner, accounts):
    yield LendingPoolPeripheral.deploy(
        lending_pool_core_contract,
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


@pytest.fixture
def buy_now_core_contract(BuyNowCore, contract_owner):
    yield BuyNowCore.deploy({"from": contract_owner})


@pytest.fixture
def buy_now_peripheral_contract(BuyNowPeripheral, buy_now_core_contract, contract_owner):
    yield BuyNowPeripheral.deploy(
        buy_now_core_contract,
        GRACE_PERIOD_DURATION,
        BUY_NOW_PERIOD_DURATION,
        AUCTION_DURATION,
        {"from": contract_owner}
    )


def test_initial_state(buy_now_peripheral_contract, buy_now_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert buy_now_peripheral_contract.owner() == contract_owner
    assert buy_now_peripheral_contract.buyNowCoreAddress() == buy_now_core_contract
    assert buy_now_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION
    assert buy_now_peripheral_contract.buyNowPeriodDuration() == BUY_NOW_PERIOD_DURATION
    assert buy_now_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION


def test_propose_owner_wrong_sender(buy_now_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        buy_now_peripheral_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        buy_now_peripheral_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(buy_now_peripheral_contract, contract_owner, borrower):
    tx = buy_now_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    assert buy_now_peripheral_contract.owner() == contract_owner
    assert buy_now_peripheral_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(buy_now_peripheral_contract, contract_owner, borrower):
    buy_now_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        buy_now_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(buy_now_peripheral_contract, contract_owner, borrower):
    buy_now_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        buy_now_peripheral_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(buy_now_peripheral_contract, contract_owner, borrower):
    buy_now_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = buy_now_peripheral_contract.claimOwnership({"from": borrower})

    assert buy_now_peripheral_contract.owner() == borrower
    assert buy_now_peripheral_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_grace_period_duration_wrong_sender(buy_now_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.setGracePeriodDuration(0, {"from": borrower})


def test_set_grace_period_duration_zero_value(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("duration is 0"):
        buy_now_peripheral_contract.setGracePeriodDuration(0, {"from": contract_owner})


def test_set_grace_period_duration(buy_now_peripheral_contract, contract_owner):
    assert buy_now_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION
    
    tx = buy_now_peripheral_contract.setGracePeriodDuration(GRACE_PERIOD_DURATION + 1, {"from": contract_owner})

    assert buy_now_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION + 1

    event = tx.events["GracePeriodDurationChanged"]
    assert event["currentValue"] == GRACE_PERIOD_DURATION
    assert event["newValue"] == GRACE_PERIOD_DURATION + 1


def test_set_grace_period_duration_same_value(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.setGracePeriodDuration(GRACE_PERIOD_DURATION, {"from": contract_owner})


def test_set_buy_now_period_duration_wrong_sender(buy_now_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.setBuyNowPeriodDuration(0, {"from": borrower})


def test_set_buy_now_period_duration_zero_value(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("duration is 0"):
        buy_now_peripheral_contract.setBuyNowPeriodDuration(0, {"from": contract_owner})


def test_set_buy_now_period_duration(buy_now_peripheral_contract, contract_owner):
    assert buy_now_peripheral_contract.buyNowPeriodDuration() == BUY_NOW_PERIOD_DURATION
    
    tx = buy_now_peripheral_contract.setBuyNowPeriodDuration(BUY_NOW_PERIOD_DURATION + 1, {"from": contract_owner})

    assert buy_now_peripheral_contract.buyNowPeriodDuration() == BUY_NOW_PERIOD_DURATION + 1

    event = tx.events["BuyNowPeriodDurationChanged"]
    assert event["currentValue"] == BUY_NOW_PERIOD_DURATION
    assert event["newValue"] == BUY_NOW_PERIOD_DURATION + 1


def test_set_buy_now_period_duration_same_value(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.setBuyNowPeriodDuration(BUY_NOW_PERIOD_DURATION, {"from": contract_owner})


def test_set_auction_period_duration_wrong_sender(buy_now_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.setAuctionPeriodDuration(0, {"from": borrower})


def test_set_auction_period_duration_zero_value(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("duration is 0"):
        buy_now_peripheral_contract.setAuctionPeriodDuration(0, {"from": contract_owner})


def test_set_auction_period_duration(buy_now_peripheral_contract, contract_owner):
    assert buy_now_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION
    
    tx = buy_now_peripheral_contract.setAuctionPeriodDuration(AUCTION_DURATION + 1, {"from": contract_owner})

    assert buy_now_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION + 1

    event = tx.events["AuctionPeriodDurationChanged"]
    assert event["currentValue"] == AUCTION_DURATION
    assert event["newValue"] == AUCTION_DURATION + 1


def test_set_auction_period_duration_same_value(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.setAuctionPeriodDuration(AUCTION_DURATION, {"from": contract_owner})


def test_set_buy_now_core_address_wrong_sender(buy_now_peripheral_contract, buy_now_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.setBuyNowCoreAddress(buy_now_core_contract, {"from": borrower})


def test_set_buy_now_core_address_zero_address(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_peripheral_contract.setBuyNowCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_buy_now_core_address_not_contract(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_peripheral_contract.setBuyNowCoreAddress(contract_owner, {"from": contract_owner})


def test_set_buy_now_core_address(buy_now_peripheral_contract, buy_now_core_contract, loans_core_contract, contract_owner):
    tx = buy_now_peripheral_contract.setBuyNowCoreAddress(loans_core_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.buyNowCoreAddress() == loans_core_contract

    event = tx.events["BuyNowCoreAddressSet"]
    assert event["currentValue"] == buy_now_core_contract
    assert event["newValue"] == loans_core_contract


def test_set_buy_now_core_address_same_address(buy_now_peripheral_contract, buy_now_core_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.setBuyNowCoreAddress(buy_now_core_contract, {"from": contract_owner})


def test_add_loans_core_address_wrong_sender(buy_now_peripheral_contract, loans_core_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": borrower})


def test_add_loans_core_address_zero_address(buy_now_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_loans_core_address_not_contract(buy_now_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_loans_core_address(buy_now_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    tx = buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    event = tx.events["LoansCoreAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_loans_core_address_same_address(buy_now_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})


def test_remove_loans_core_address_wrong_sender(buy_now_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.removeLoansCoreAddress(erc20_contract, {"from": borrower})


def test_remove_loans_core_address_zero_address(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        buy_now_peripheral_contract.removeLoansCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_loans_core_address_not_contract(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        buy_now_peripheral_contract.removeLoansCoreAddress(contract_owner, {"from": contract_owner})


def test_remove_loans_core_address_not_found(buy_now_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        buy_now_peripheral_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})


def test_remove_loans_core_address(buy_now_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    tx = buy_now_peripheral_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.loansCoreAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LoansCoreAddressRemoved"]
    assert event["currentValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_lending_pool_peripheral_address_wrong_sender(buy_now_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": borrower})


def test_add_lending_pool_peripheral_address_zero_address(buy_now_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_lending_pool_peripheral_address_not_contract(buy_now_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_lending_pool_peripheral_address(buy_now_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    tx = buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract

    event = tx.events["LendingPoolPeripheralAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == lending_pool_peripheral_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_lending_pool_peripheral_address_same_address(buy_now_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract

    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address_wrong_sender(buy_now_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, {"from": borrower})


def test_remove_lending_pool_peripheral_address_zero_address(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        buy_now_peripheral_contract.removeLendingPoolPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address_not_contract(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        buy_now_peripheral_contract.removeLendingPoolPeripheralAddress(contract_owner, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address_not_found(buy_now_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        buy_now_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address(buy_now_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract

    tx = buy_now_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LendingPoolPeripheralAddressRemoved"]
    assert event["currentValue"] == lending_pool_peripheral_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_set_collateral_vault_address_wrong_sender(buy_now_peripheral_contract, collateral_vault_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": borrower})


def test_set_collateral_vault_address_zero_address(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_collateral_vault_address(buy_now_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    tx = buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    event = tx.events["CollateralVaultPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == collateral_vault_peripheral_contract


def test_set_collateral_vault_address_same_address(buy_now_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert buy_now_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    with brownie.reverts("new value is the same"):
        buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})


def test_add_liquidation_zero_values(buy_now_peripheral_contract, buy_now_core_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc20_contract, erc721_contract, contract_owner, borrower):
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    
    with brownie.reverts("collat addr is the zero addr"):
        buy_now_peripheral_contract.addLiquidation(
            brownie.ZERO_ADDRESS,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )
    
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    with brownie.reverts("principal is 0"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )
    
    with brownie.reverts("interestAmount is 0"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            PRINCIPAL,
            0,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )
    
    with brownie.reverts("apr is 0"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            PRINCIPAL,
            INTEREST_AMOUNT,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )
    
    with brownie.reverts("borrower is the zero addr"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )
    
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            0,
            brownie.ZERO_ADDRESS
        )


def test_add_liquidation_collat_not_contract(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("collat addr is not a contract"):
        buy_now_peripheral_contract.addLiquidation(
            contract_owner,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )


def test_add_liquidation_collat_not_nft(buy_now_peripheral_contract, erc20_contract):
    with brownie.reverts(""):
        buy_now_peripheral_contract.addLiquidation(
            erc20_contract,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )


def test_add_liquidation_collat_not_owned_by_vault(buy_now_peripheral_contract, buy_now_core_contract, collateral_vault_peripheral_contract, erc721_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by vault"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )


def test_add_liquidation(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    tx = buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            0,
            erc20_contract
        )

    liquidation = buy_now_peripheral_contract.getLiquidation(erc721_contract, 0)

    assert liquidation["gracePeriodMaturity"] == liquidation["startTime"] + GRACE_PERIOD_DURATION
    assert liquidation["buyNowPeriodMaturity"] == liquidation["startTime"] + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION
    assert liquidation["principal"] == PRINCIPAL
    assert liquidation["interestAmount"] == INTEREST_AMOUNT
    assert liquidation["apr"] == APR
    assert liquidation["borrower"] == borrower
    assert liquidation["erc20TokenContract"] == erc20_contract

    event = tx.events["LiquidationAdded"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["erc20TokenContract"] == erc20_contract
    assert event["gracePeriodPrice"] == int(Decimal(PRINCIPAL) + Decimal(INTEREST_AMOUNT) + Decimal(PRINCIPAL * APR * 2) / Decimal(365))
    assert event["buyNowPeriodPrice"] == int(Decimal(PRINCIPAL) + Decimal(INTEREST_AMOUNT) + Decimal(PRINCIPAL * APR * 17) / Decimal(365))


def test_add_liquidation_loan_not_defaulted(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value

    with brownie.reverts("loan is not defaulted"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            0,
            erc20_contract
        )


def test_add_liquidation_collat_not_in_loan(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    erc721_contract.mint(collateral_vault_core_contract, 1, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    with brownie.reverts("collateral not in loan"):
        buy_now_peripheral_contract.addLiquidation(
            erc721_contract,
            1,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            borrower,
            0,
            erc20_contract
        )


def test_buy_nft_collat_not_contract(buy_now_peripheral_contract, contract_owner):
    with brownie.reverts("collat addr is not a contract"):
        buy_now_peripheral_contract.buyNFT(
            contract_owner,
            0
        )


def test_buy_nft_collat_not_nft(buy_now_peripheral_contract, erc20_contract):
    with brownie.reverts(""):
        buy_now_peripheral_contract.buyNFT(
            erc20_contract,
            0
        )


def test_buy_nft_collat_not_owned_by_vault(buy_now_peripheral_contract, buy_now_core_contract, collateral_vault_peripheral_contract, erc721_contract, contract_owner):
    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by vault"):
        buy_now_peripheral_contract.buyNFT(
            erc721_contract,
            0
        )


def test_buy_nft_not_allowed(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, lending_pool_peripheral_contract, lending_pool_core_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    buy_now_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        borrower,
        0,
        erc20_contract
    )

    with brownie.reverts("msg.sender is not borrower"):
        buy_now_peripheral_contract.buyNFT(
            erc721_contract,
            0,
            {"from": contract_owner}
        )

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION + 1)

    with brownie.reverts("msg.sender is not a lender"):
        buy_now_peripheral_contract.buyNFT(
            erc721_contract,
            0,
            {"from": contract_owner}
        )
    
    chain.mine(blocks=1, timedelta=BUY_NOW_PERIOD_DURATION + 1)

    with brownie.reverts("liquidation out of buying period"):
        buy_now_peripheral_contract.buyNFT(
            erc721_contract,
            0,
            {"from": contract_owner}
        )


def test_buy_nft_grace_period(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, lending_pool_peripheral_contract, lending_pool_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, PRINCIPAL * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, PRINCIPAL * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(PRINCIPAL * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, PRINCIPAL, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    buy_now_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        borrower,
        0,
        erc20_contract
    )

    grace_period_price = int(Decimal(PRINCIPAL) + Decimal(INTEREST_AMOUNT) + Decimal(PRINCIPAL * APR * 2) / Decimal(365))
    erc20_contract.mint(borrower, grace_period_price, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, grace_period_price, {"from": borrower})

    tx = buy_now_peripheral_contract.buyNFT(
        erc721_contract,
        0,
        {"from": borrower}
    )

    liquidation = buy_now_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

    event = tx.events["LiquidationRemoved"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["erc20TokenContract"] == erc20_contract

    event = tx.events["NFTPurchased"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["amount"] == grace_period_price
    assert event["erc20TokenContract"] == erc20_contract


def test_buy_nft_buynow_period(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, lending_pool_peripheral_contract, lending_pool_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    buy_now_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, PRINCIPAL * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, PRINCIPAL * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(PRINCIPAL * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, PRINCIPAL, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    buy_now_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        borrower,
        0,
        erc20_contract
    )

    buy_now_period_price = int(Decimal(PRINCIPAL) + Decimal(INTEREST_AMOUNT) + Decimal(PRINCIPAL * APR * 17) / Decimal(365))
    erc20_contract.mint(contract_owner, buy_now_period_price, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, buy_now_period_price, {"from": contract_owner})

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION + 1)

    tx = buy_now_peripheral_contract.buyNFT(
        erc721_contract,
        0,
        {"from": contract_owner}
    )

    liquidation = buy_now_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

    event = tx.events["LiquidationRemoved"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["erc20TokenContract"] == erc20_contract

    event = tx.events["NFTPurchased"]
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["amount"] == buy_now_period_price
    assert event["erc20TokenContract"] == erc20_contract
