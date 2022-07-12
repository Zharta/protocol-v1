from brownie.network import chain
from datetime import datetime as dt
from web3 import Web3

import brownie
import pytest


GRACE_PERIOD_DURATION = 172800 # 2 days
BUY_NOW_PERIOD_DURATION = 604800 # 15 days
AUCTION_DURATION = 604800 # 15 days

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
def collateral_vault_contract(accounts):
    yield accounts[2]


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


def test_add_liquidation_zero_values(buy_now_peripheral_contract, buy_now_core_contract, loans_core_contract, collateral_vault_contract, erc20_contract, erc721_contract, contract_owner, borrower):
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
    
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})
    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})
    
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


def test_add_liquidation_collat_not_owned_by_vault(buy_now_peripheral_contract, buy_now_core_contract, collateral_vault_contract, erc721_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})

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


def test_add_liquidation(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, lending_pool_peripheral_contract, collateral_vault_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    
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


def test_add_liquidation_loan_not_defaulted(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, lending_pool_peripheral_contract, collateral_vault_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    
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


def test_add_liquidation_collat_not_in_loan(buy_now_peripheral_contract, buy_now_core_contract, loans_peripheral_contract, loans_core_contract, lending_pool_peripheral_contract, collateral_vault_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    buy_now_core_contract.setCollateralVaultAddress(collateral_vault_contract, {"from": contract_owner})
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    buy_now_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_contract, 0, {"from": contract_owner})
    erc721_contract.mint(collateral_vault_contract, 1, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    
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




