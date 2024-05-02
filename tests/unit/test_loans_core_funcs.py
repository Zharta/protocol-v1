import boa
import pytest

MATURITY = 123456789
LOAN_AMOUNT = 10**17
LOAN_INTEREST = 250


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc721():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def loans_core(loans_core_contract, path_to_erc20_mock, contract_owner):
    with boa.env.prank(contract_owner):
        contract = loans_core_contract.deploy()
        contract.setLoansPeripheral(path_to_erc20_mock.deploy())
        return contract


@pytest.fixture(scope="module")
def test_collaterals(erc721):
    return [(erc721, k, LOAN_AMOUNT // 5) for k in range(5)]


def test_add_loan(loans_core, borrower, contract_owner, test_collaterals):
    loan_id = loans_core.addLoan(
        borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_core.loansPeripheral()
    )

    assert loan_id == 0

    assert loans_core.getLoanAmount(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core.getLoanInterest(borrower, loan_id) == LOAN_INTEREST
    assert loans_core.getLoanMaturity(borrower, loan_id) == MATURITY
    assert loans_core.getLoanPaidPrincipal(borrower, loan_id) == 0
    assert loans_core.getLoanPaidInterestAmount(borrower, loan_id) == 0
    assert not loans_core.getLoanStarted(borrower, loan_id)
    assert len(loans_core.getLoanCollaterals(borrower, loan_id)) == len(test_collaterals)
    assert loans_core.getLoanCollaterals(borrower, loan_id) == test_collaterals

    loan = loans_core.getPendingLoan(borrower, loan_id)
    assert loans_core.getLoanAmount(borrower, loan_id) == loan[1]
    assert loans_core.getLoanInterest(borrower, loan_id) == loan[2]
    assert loans_core.getLoanMaturity(borrower, loan_id) == loan[3]
    assert loans_core.getLoanPaidPrincipal(borrower, loan_id) == loan[6]
    assert loans_core.getLoanPaidInterestAmount(borrower, loan_id) == loan[7]
    assert loans_core.getLoanStarted(borrower, loan_id) == loan[8]
    assert loans_core.getLoanInvalidated(borrower, loan_id) == loan[9]
    assert loans_core.getLoanPaid(borrower, loan_id) == loan[10]
    assert loans_core.getLoanDefaulted(borrower, loan_id) == loan[11]
    assert loans_core.getLoanCanceled(borrower, loan_id) == loan[12]

    pending_loan_collaterals = loans_core.getPendingLoan(borrower, loan_id)[5]
    assert len(pending_loan_collaterals) == len(test_collaterals)
    assert pending_loan_collaterals == test_collaterals

    assert loans_core.borrowedAmount(borrower) == 0

    assert loans_core.ongoingLoans(borrower) == 1


def test_update_paid_loan_wrong_sender(loans_core, contract_owner, borrower):
    with boa.reverts("msg.sender is not the loans addr"):
        loans_core.updatePaidLoan(borrower, 0, sender=contract_owner)


def test_update_paid_loan(loans_core, erc721, borrower, contract_owner, test_collaterals):
    loans_peripheral = loans_core.loansPeripheral()

    loan_id = loans_core.addLoan(borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_peripheral)

    loans_core.updateLoanStarted(borrower, loan_id, sender=loans_peripheral)

    loans_core.updatePaidLoan(borrower, loan_id, sender=loans_peripheral)
    assert loans_core.getLoanPaid(borrower, loan_id) == loans_core.getLoan(borrower, loan_id)[10]
    assert loans_core.getLoanPaid(borrower, loan_id)

    assert loans_core.borrowedAmount(borrower) == 0
    assert loans_core.collectionsBorrowedAmount(erc721) == 0

    assert loans_core.ongoingLoans(borrower) == 0


def test_update_defaulted_loan_wrong_sender(loans_core, contract_owner, borrower):
    with boa.reverts("msg.sender is not the loans addr"):
        loans_core.updateDefaultedLoan(borrower, 0, sender=contract_owner)


def test_update_defaulted_loan(loans_core, erc721, borrower, contract_owner, test_collaterals):
    loans_peripheral = loans_core.loansPeripheral()

    loan_id = loans_core.addLoan(borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_peripheral)

    loans_core.updateLoanStarted(borrower, loan_id, sender=loans_peripheral)

    loans_core.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral)
    assert loans_core.getLoanDefaulted(borrower, loan_id) == loans_core.getLoan(borrower, loan_id)[11]
    assert loans_core.getLoanDefaulted(borrower, loan_id)

    assert loans_core.borrowedAmount(borrower) == 0
    assert loans_core.collectionsBorrowedAmount(erc721) == 0

    assert loans_core.ongoingLoans(borrower) == 0


def test_update_loan_started_wrong_sender(loans_core, contract_owner, borrower, test_collaterals):
    loan_id = loans_core.addLoan(
        borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_core.loansPeripheral()
    )

    with boa.reverts("msg.sender is not the loans addr"):
        loans_core.updateLoanStarted(borrower, loan_id, sender=contract_owner)


def test_update_loan_started(loans_core, erc721, contract_owner, borrower, test_collaterals):
    loan_id = loans_core.addLoan(
        borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_core.loansPeripheral()
    )

    loans_core.updateLoanStarted(borrower, loan_id, sender=loans_core.loansPeripheral())

    assert loans_core.getLoanAmount(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core.getLoanInterest(borrower, loan_id) == LOAN_INTEREST
    assert loans_core.getLoanMaturity(borrower, loan_id) == MATURITY
    assert loans_core.getLoanStarted(borrower, loan_id)
    assert len(loans_core.getLoanCollaterals(borrower, loan_id)) == len(test_collaterals)
    assert loans_core.getLoanCollaterals(borrower, loan_id) == test_collaterals

    assert loans_core.borrowedAmount(borrower) == LOAN_AMOUNT
    assert loans_core.collectionsBorrowedAmount(erc721) == LOAN_AMOUNT


def test_update_paid_amount_wrong_sender(loans_core, contract_owner, borrower, test_collaterals):
    loan_id = loans_core.addLoan(
        borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_core.loansPeripheral()
    )

    loans_core.updateLoanStarted(borrower, loan_id, sender=loans_core.loansPeripheral())

    with boa.reverts("msg.sender is not the loans addr"):
        loans_core.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT, 0, sender=contract_owner)


def test_update_paid_amount(loans_core, contract_owner, borrower, test_collaterals):
    loan_id = loans_core.addLoan(
        borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_core.loansPeripheral()
    )

    loans_core.updateLoanStarted(borrower, loan_id, sender=loans_core.loansPeripheral())

    loans_core.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT, 0, sender=loans_core.loansPeripheral())

    assert loans_core.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core.getLoanPaidInterestAmount(borrower, loan_id) == 0


def test_update_paid_amount_multiple(loans_core, contract_owner, borrower, test_collaterals):
    loan_id = loans_core.addLoan(
        borrower, LOAN_AMOUNT, LOAN_INTEREST, MATURITY, test_collaterals, sender=loans_core.loansPeripheral()
    )

    loans_core.updateLoanStarted(borrower, loan_id, sender=loans_core.loansPeripheral())

    loans_core.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT // 2, 0, sender=loans_core.loansPeripheral())

    assert loans_core.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT // 2

    loans_core.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT // 2, 0, sender=loans_core.loansPeripheral())

    assert loans_core.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core.getLoanPaidInterestAmount(borrower, loan_id) == 0
