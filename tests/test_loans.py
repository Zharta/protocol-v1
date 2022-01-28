import pytest
import datetime as dt
import brownie
import time

from web3 import Web3
from decimal import Decimal

MAX_NUMBER_OF_LOANS = 10
TEST_COLLATERAL_IDS = list(range(5)) + [0] * 5
MATURITY = int(dt.datetime.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


@pytest.fixture
def contract_owner(accounts):
    yield accounts[0]


@pytest.fixture
def borrower(accounts):
    yield accounts[1]


@pytest.fixture
def investor(accounts):
    yield accounts[2]


@pytest.fixture
def erc20_contract(ERC20PresetMinterPauser, contract_owner):
    yield ERC20PresetMinterPauser.deploy("USD Coin", "USDC", {'from': contract_owner})


@pytest.fixture
def erc721_contract(ERC721PresetMinterPauserAutoId, contract_owner):
    yield ERC721PresetMinterPauserAutoId.deploy(
        "VeeFriends",
        "VEE",
        "tokenURI",
        {'from': contract_owner}
    )


@pytest.fixture
def loans_contract(Loans, contract_owner):
    yield Loans.deploy(MAX_NUMBER_OF_LOANS, {'from': contract_owner})


@pytest.fixture
def lending_pool_contract(LendingPool, loans_contract, erc20_contract, contract_owner):
    yield LendingPool.deploy(loans_contract.address, erc20_contract, {"from": contract_owner})


def test_initial_state(loans_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_contract.owner() == contract_owner
    assert loans_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS


def test_set_lending_pool_address_not_owner(loans_contract, lending_pool_contract, borrower):
    with brownie.reverts("Only the contract owner can set the investment pool address"):
        loans_contract.setLendingPoolAddress(
            lending_pool_contract.address,
            {"from": borrower}
        )


def test_set_lending_pool_address(loans_contract, lending_pool_contract, contract_owner):
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )


def test_add_address_to_whitelist_wrong_sender(loans_contract, erc721_contract, borrower):
    with brownie.reverts("Only the contract owner can add collateral addresses to the whitelist"):
        loans_contract.addCollateralToWhitelist(
            erc721_contract.address,
            {"from": borrower}
        )


def test_add_address_to_whitelist_not_contract_address(loans_contract, contract_owner):
    with brownie.reverts("The _address sent does not have a contract deployed"):
        loans_contract.addCollateralToWhitelist(
            "0xa3aee8bce55beea1951ef834b99f3ac60d1abeeb",
            {"from": contract_owner}
        )


def test_add_address_to_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(
        erc721_contract.address,
        {"from": contract_owner}
    )

    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == erc721_contract.address


def test_remove_address_from_whitelist_wrong_sender(loans_contract, erc721_contract, contract_owner, borrower):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("Only the contract owner can add collateral addresses to the whitelist"):
        loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": borrower})


def test_remove_address_from_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})

    assert loans_contract.whitelistedCollaterals(erc721_contract.address) != erc721_contract.address


def test_new_loan_unauthorized(loans_contract, erc721_contract, borrower):
    with brownie.reverts("Only the contract owner can create loans"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
            TEST_COLLATERAL_IDS,
            {'from': borrower}
        )


def test_newloan_collateral_notwhitelisted(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("The collaterals are not all whitelisted"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
            TEST_COLLATERAL_IDS,
            {'from': contract_owner}
        )


def test_newloan_maturity_in_the_past(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower
):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    maturity = int(dt.datetime.now().timestamp()) - 3600
    with brownie.reverts("Maturity can not be in the past"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
            [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
            TEST_COLLATERAL_IDS,
            {'from': contract_owner}
        )

def test_newloan_collaterals_already_used(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower
):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    with brownie.reverts("One of the submitted collaterals is already being used"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
            TEST_COLLATERAL_IDS,
            {'from': contract_owner}
        )


def test_newloan(loans_contract, erc721_contract, contract_owner, borrower):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    next_loan_id = loans_contract.nextLoanId(borrower)
    assert next_loan_id == 1
    loan_details = loans_contract.loans(borrower, next_loan_id - 1)

    assert loan_details["id"] == next_loan_id - 1
    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["maturity"] == MATURITY
    assert loan_details["collaterals"]["size"] == 5
    assert loan_details["collaterals"]["contracts"] == [erc721_contract.address] * 5 + [
        "0x0000000000000000000000000000000000000000"] * 5
    assert loan_details["collaterals"]["ids"] == TEST_COLLATERAL_IDS
    assert loan_details["approved"] == True
    assert loan_details["issued"] == False

    assert loans_contract.currentApprovedLoans() == 1
    assert loans_contract.totalApprovedLoans() == 1


def test_start_loan_not_approved(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("The sender does not have an approved loan"):
        loans_contract.start(0, {"from": borrower})


def test_start_loan_already_started(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan = tx.return_value

    loans_contract.start(loan["id"], {"from": borrower})

    with brownie.reverts("The sender already started the loan"):
        loans_contract.start(loan["id"], {"from": borrower})


def test_start_loan_collateral_not_approved(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    with brownie.reverts("The collaterals are not all approved to be transferred"):
        loans_contract.start(tx.return_value["id"], {"from": borrower})


def test_start_loan(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_details = tx_new_loan.return_value

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_start_loan = loans_contract.start(loan_details["id"], {"from": borrower})
    loan_details = tx_start_loan.return_value

    assert loan_details["id"] == 0
    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["maturity"] == MATURITY
    assert loan_details["collaterals"]["size"] == 5
    assert loan_details["collaterals"]["contracts"] == [erc721_contract.address] * 5 + [
        "0x0000000000000000000000000000000000000000"] * 5
    assert loan_details["collaterals"]["ids"] == TEST_COLLATERAL_IDS
    assert loan_details["approved"] == True
    assert loan_details["issued"] == True

    assert loans_contract.currentApprovedLoans() == 1
    assert loans_contract.totalApprovedLoans() == 1
    assert loans_contract.currentIssuedLoans() == 1
    assert loans_contract.totalIssuedLoans() == 1

    assert len(tx_start_loan.events) == 13
    assert tx_start_loan.events[-1]["borrower"] == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == loans_contract.address


def test_pay_loan_not_issued(loans_contract, borrower):
    with brownie.reverts("The sender does not have an issued loan"):
        loans_contract.pay(0, LOAN_AMOUNT * (100 + LOAN_INTEREST) / 100, {"from": borrower})


def test_pay_loan_no_value_sent(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan = tx.return_value

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.start(loan["id"], {"from": borrower})

    with brownie.reverts("The amount paid needs to be higher than 0"):
        loans_contract.pay(loan["id"], 0, {"from": borrower})


def test_pay_loan_higher_value_than_needed(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan = tx.return_value

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.start(loan["id"], {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}") + 10000)
    
    with brownie.reverts("The amount paid is higher than the amount left to be paid"):
        loans_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_defaulted(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        int(dt.datetime.now().timestamp()) + 5,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan = tx.return_value

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.start(loan["id"], {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    time.sleep(5)
    with brownie.reverts("The maturity of the loan has already been reached and it defaulted"):
        loans_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_insufficient_balance(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx_new_loan.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, (amount_paid - LOAN_AMOUNT) / 2, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    loans_contract.start(loan_id, {"from": borrower})
    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    
    with brownie.reverts("User has insufficient balance for the payment"):
        tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan_insufficient_allowance(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx_new_loan.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    loans_contract.start(loan_id, {"from": borrower})
    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_contract, amount_paid / 2, {"from": borrower})
    
    with brownie.reverts("User did not allow funds to be transferred"):
        tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx_new_loan.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    loans_contract.start(loan_id, {"from": borrower})
    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    empty_loan = tx_pay_loan.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.currentIssuedLoans() == 0
    assert loans_contract.totalPaidLoans() == 1

    assert len(tx_pay_loan.events) == 14
    assert tx_pay_loan.events[-1]["borrower"] == borrower

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - amount_paid


def test_pay_loan_multiple(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx_new_loan.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    
    erc20_contract.mint(borrower, 2 * amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    loans_contract.start(loan_id, {"from": borrower})
    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    loan_details = loans_contract.loans(borrower, loan_id)
    assert loan_details["paidAmount"] == amount_paid
    assert loans_contract.currentApprovedLoans() == 1
    assert loans_contract.currentIssuedLoans() == 1
    assert loans_contract.totalPaidLoans() == 0

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == loans_contract.address
    
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    empty_loan = tx_pay_loan.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.currentIssuedLoans() == 0
    assert loans_contract.totalPaidLoans() == 1

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - amount_paid * 2


def test_set_default_loan_wrong_sender(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.start(loan_id, {"from": borrower})

    with brownie.reverts("Only the contract owner can default loans"):
        loans_contract.settleDefault(borrower, loan_id, {"from": investor})


def test_set_default_loan_not_started(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    with brownie.reverts("The sender does not have an issued loan"):
        loans_contract.settleDefault(borrower, loan_id, {"from": contract_owner})


def test_set_default_loan(
    loans_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        int(dt.datetime.now().timestamp() + 5),
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx_new_loan.return_value["id"]

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.start(loan_id, {"from": borrower})

    time.sleep(5)
    tx_default_loan = loans_contract.settleDefault(borrower, loan_id, {"from": contract_owner})

    empty_loan = tx_default_loan.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.totalApprovedLoans() == 1
    assert loans_contract.currentIssuedLoans() == 0
    assert loans_contract.totalIssuedLoans() == 1
    assert loans_contract.totalDefaultedLoans() == 1

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == contract_owner


def test_cancel_approved_loan_not_approved(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower
):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx.return_value["id"]

    with brownie.reverts("The sender does not have an approved loan"):
        loans_contract.cancel(loan_id, {"from": contract_owner})


def test_cancel_approved_loan(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower
):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    tx_new_loan = loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )
    loan_id = tx_new_loan.return_value["id"]

    tx_cancel_loan = loans_contract.cancel(loan_id, {"from": borrower})

    empty_loan = tx_cancel_loan.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.totalApprovedLoans() == 1

    assert len(tx_cancel_loan.events) == 1
    assert tx_cancel_loan.events[0]["borrower"] == borrower
