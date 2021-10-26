import pytest
import datetime as dt
import brownie
import time

from web3 import Web3
from decimal import Decimal
from Crypto.Hash import keccak


TEST_COLLATERAL_IDS = list(range(5)) + [0] * 5
MATURITY = int(dt.datetime.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250 # 2.5% in parts per 10000


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
def loans_contract(Loans, contract_owner):
    yield Loans.deploy({'from': contract_owner})


@pytest.fixture
def erc721_contract(ERC721PresetMinterPauserAutoId, contract_owner):
    yield ERC721PresetMinterPauserAutoId.deploy(
        "VeeFriends",
        "VEE",
        "tokenURI",
        {'from': contract_owner}
    )


@pytest.fixture
def investmentpool_contract(InvestmentPool, loans_contract, contract_owner):
    yield InvestmentPool.deploy(loans_contract.address, {"from": contract_owner})


def test_initial_state(loans_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_contract.owner() == contract_owner


def test_set_invpool_address_notowner(loans_contract, investmentpool_contract, borrower):
    with brownie.reverts("Only the contract owner can set the investment pool address!"):
        loans_contract.setInvestmentPoolAddress(
            investmentpool_contract.address,
            {"from": borrower}
        )


def test_set_invpool_address(loans_contract, investmentpool_contract, contract_owner):
    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )


def test_add_address_to_whitelist_wrong_sender(loans_contract, erc721_contract, borrower):
    with brownie.reverts("Only the contract owner can add collateral addresses to the whitelist!"):
        loans_contract.addCollateralToWhitelist(
            erc721_contract.address,
            {"from": borrower}
        )


def test_add_address_to_whitelist_not_contract_address(loans_contract, contract_owner):
    with brownie.reverts("The _address sent does not have a contract deployed!"):
        loans_contract.addCollateralToWhitelist(
            "0xa3aee8bce55beea1951ef834b99f3ac60d1abeeb",
            {"from": contract_owner}
        )


def test_add_address_to_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(
        erc721_contract.address,
        {"from": contract_owner}
    )

    assert loans_contract.isCollateralWhitelisted(erc721_contract.address) == True


def test_remove_address_from_whitelist_wrong_sender(loans_contract, erc721_contract, contract_owner, borrower):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("Only the contract owner can add collateral addresses to the whitelist!"):
        loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": borrower})


def test_remove_address_from_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})

    assert loans_contract.isCollateralWhitelisted(erc721_contract.address) == False


def test_new_loan_unauthorized(loans_contract, erc721_contract, borrower):
    with brownie.reverts("Only the contract owner can create loans!"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
            TEST_COLLATERAL_IDS,
            {'from': borrower}
        )


def test_newloan_sender_already_has_loan(
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

    with brownie.reverts("The sender already has an approved loan!"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
            TEST_COLLATERAL_IDS,
            {'from': contract_owner}
        )


def test_newloan_collateral_notwhitelisted(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("The collaterals are not all whitelisted!"):
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
    with brownie.reverts("Maturity can not be in the past!"):
        loans_contract.newLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
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

    loan_details = loans_contract.loanDetails({'from': borrower})

    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["paidAmountInterest"] == 0
    assert loan_details["maturity"] == MATURITY
    assert loan_details["collaterals"]["size"] == 5
    assert loan_details["collaterals"]["contracts"] == [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5
    assert loan_details["collaterals"]["ids"] == TEST_COLLATERAL_IDS
    assert loan_details["approved"] == True
    assert loan_details["issued"] == False
    assert loan_details["defaulted"] == False
    assert loan_details["paid"] == False

    assert loans_contract.currentApprovedLoans() == 1
    assert loans_contract.totalApprovedLoans() == 1


def test_unauthorized_access_approved_loans(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor
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
    with brownie.reverts("The sender does not have an approved loan!"):
        loans_contract.loanDetails({'from': investor})


def test_start_loan_not_approved(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("The sender does not have an approved loan!"):
        loans_contract.startApprovedLoan({"from": borrower})


def test_start_loan_collateral_not_approved(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})

    loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    with brownie.reverts("The collaterals are not all approved to be transferred!"):
        loans_contract.startApprovedLoan({"from": borrower})


def test_start_loan(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    borrower,
    investor
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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
    
    borrower_initial_balance = borrower.balance()

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx = loans_contract.startApprovedLoan({"from": borrower})

    loan_details = tx.return_value

    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["paidAmountInterest"] == 0
    assert loan_details["maturity"] == MATURITY
    assert loan_details["collaterals"]["size"] == 5
    assert loan_details["collaterals"]["contracts"] == [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5
    assert loan_details["collaterals"]["ids"] == TEST_COLLATERAL_IDS
    assert loan_details["approved"] == True
    assert loan_details["issued"] == True
    assert loan_details["defaulted"] == False
    assert loan_details["paid"] == False

    assert loans_contract.currentApprovedLoans() == 1
    assert loans_contract.totalApprovedLoans() == 1
    assert loans_contract.currentIssuedLoans() == 1
    assert loans_contract.totalIssuedLoans() == 1

    assert len(tx.events) == 12
    assert tx.events[11]["borrower"] == borrower

    assert borrower.balance() == borrower_initial_balance + LOAN_AMOUNT

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == loans_contract.address


def test_pay_loan_not_issued(loans_contract, borrower):
    with brownie.reverts("The sender does not have an issued loan!"):
        loans_contract.payLoan({"from": borrower, "value": LOAN_AMOUNT * (100 + LOAN_INTEREST) / 100})


def test_pay_loan_no_value_sent(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.startApprovedLoan({"from": borrower})

    with brownie.reverts("The value sent needs to be higher than 0!"):
        loans_contract.payLoan({"from": borrower})

def test_pay_loan_higher_value_than_needed(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.startApprovedLoan({"from": borrower})

    with brownie.reverts("The value sent is higher than the amount left to be paid!"):
        amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}") + 1)
        loans_contract.payLoan({"from": borrower, "value": amount_paid})


def test_pay_loan_defaulted(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        int(dt.datetime.now().timestamp()) + 10,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.startApprovedLoan({"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    time.sleep(10)
    with brownie.reverts("The maturity of the loan has already been reached. The loan is defaulted!"):
        loans_contract.payLoan({"from": borrower, "value": amount_paid})


def test_pay_loan_multiple(
   loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    borrower,
    investor
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    borrower_initial_balance = borrower.balance()

    loans_contract.startApprovedLoan({"from": borrower})
    borrower_amount_after_loan_started = borrower.balance()

    assert borrower.balance() == borrower_initial_balance + LOAN_AMOUNT

    amount_paid = int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    loans_contract.payLoan({"from": borrower, "value": amount_paid})

    loan_details = loans_contract.loanDetails({"from": borrower})
    assert loan_details["paidAmount"] == int(Decimal(f"{LOAN_AMOUNT / 2.0}"))
    assert loan_details["paidAmountInterest"] == int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(LOAN_INTEREST) / 10000}"))
    assert loans_contract.currentApprovedLoans() == 1
    assert loans_contract.currentIssuedLoans() == 1
    assert loans_contract.totalPaidLoans() == 0

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == loans_contract.address

    amount_paid = int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    tx = loans_contract.payLoan({"from": borrower, "value": amount_paid})

    empty_loan = tx.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0
    assert empty_loan["paidAmountInterest"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.currentIssuedLoans() == 0
    assert loans_contract.totalPaidLoans() == 1

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == borrower

    assert borrower.balance() == borrower_amount_after_loan_started - amount_paid * 2


def test_pay_loan(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    borrower,
    investor
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    borrower_initial_balance = borrower.balance()

    loans_contract.startApprovedLoan({"from": borrower})
    borrower_amount_after_loan_started = borrower.balance()

    assert borrower.balance() == borrower_initial_balance + LOAN_AMOUNT

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    tx = loans_contract.payLoan({"from": borrower, "value": amount_paid})

    empty_loan = tx.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0
    assert empty_loan["paidAmountInterest"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.currentIssuedLoans() == 0
    assert loans_contract.totalPaidLoans() == 1

    assert len(tx.events) == 12
    assert tx.events[11]["borrower"] == borrower

    for collateral_id in TEST_COLLATERAL_IDS:
        assert erc721_contract.ownerOf(collateral_id) == borrower

    assert borrower.balance() == borrower_amount_after_loan_started - amount_paid


def test_set_default_loan_wrong_sender(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.startApprovedLoan({"from": borrower})

    with brownie.reverts("Only the contract owner can default loans!"):
        loans_contract.settleDefaultedLoan(borrower, {"from": investor})


def test_set_default_loan_not_started(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

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

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    with brownie.reverts("The sender does not have an issued loan!"):
        loans_contract.settleDefaultedLoan(borrower, {"from": contract_owner})


def test_set_default_loan(
    loans_contract,
    erc721_contract,
    investmentpool_contract,
    contract_owner,
    investor,
    borrower
):
    investmentpool_contract.invest({"from": investor, "value": "1 ether"})

    loans_contract.setInvestmentPoolAddress(
        investmentpool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        int(dt.datetime.now().timestamp() + 10),
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    loans_contract.startApprovedLoan({"from": borrower})

    time.sleep(10)
    tx = loans_contract.settleDefaultedLoan(borrower, {"from": contract_owner})

    empty_loan = tx.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0
    assert empty_loan["paidAmountInterest"] == 0

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

    loans_contract.newLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [erc721_contract.address] * 5 + ["0x0000000000000000000000000000000000000000"] * 5,
        TEST_COLLATERAL_IDS,
        {'from': contract_owner}
    )

    with brownie.reverts("The sender does not have an approved loan!"):
        loans_contract.cancelApprovedLoan({"from": contract_owner})


def test_cancel_approved_loan(
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

    tx = loans_contract.cancelApprovedLoan({"from": borrower})

    empty_loan = tx.return_value
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0
    assert empty_loan["paidAmountInterest"] == 0

    assert empty_loan["collaterals"]["size"] == 0
    for k in range(len(TEST_COLLATERAL_IDS)):
        assert empty_loan["collaterals"]["contracts"][k] == "0x0000000000000000000000000000000000000000"
        assert empty_loan["collaterals"]["ids"][k] == 0

    assert loans_contract.currentApprovedLoans() == 0
    assert loans_contract.totalApprovedLoans() == 1

    assert len(tx.events) == 1
    assert tx.events[0]["borrower"] == borrower
