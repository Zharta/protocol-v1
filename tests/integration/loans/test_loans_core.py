import datetime as dt
import boa
from web3 import Web3

from ..conftest_base import ZERO_ADDRESS, get_last_event, checksummed

MATURITY = int(dt.datetime.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.to_wei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


def test_set_loans_peripheral(loans_core_contract, loans_peripheral_contract, contract_owner):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, sender=contract_owner)
    event = get_last_event(loans_core_contract, name="LoansPeripheralAddressSet")

    assert loans_core_contract.loansPeripheral() == loans_peripheral_contract.address
    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_peripheral_contract.address


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(loans_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(loans_core_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_core_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(loans_core_contract, contract_owner):
    with boa.reverts("_address it the zero address"):
        loans_core_contract.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(loans_core_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        loans_core_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(contracts_config, loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(loans_core_contract, name="OwnerProposed")

    assert loans_core_contract.proposedOwner() == borrower
    assert loans_core_contract.owner() == contract_owner
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(contracts_config, loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        loans_core_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        loans_core_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.proposeOwner(borrower, sender=contract_owner)

    loans_core_contract.claimOwnership(sender=borrower)
    event = get_last_event(loans_core_contract, name="OwnershipTransferred")

    assert loans_core_contract.owner() == borrower
    assert loans_core_contract.proposedOwner() == ZERO_ADDRESS
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_loans_peripheral_wrong_sender(loans_core_contract, loans_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_core_contract.setLoansPeripheral(loans_peripheral_contract, sender=borrower)


def test_set_loans_peripheral_zero_address(loans_core_contract, contract_owner):
    with boa.reverts("_address is the zero address"):
        loans_core_contract.setLoansPeripheral(ZERO_ADDRESS, sender=contract_owner)


def test_set_loans_peripheral_same_address(loans_core_contract, loans_peripheral_contract, contract_owner):
    with boa.reverts("new loans addr is the same"):
        loans_core_contract.setLoansPeripheral(loans_peripheral_contract, sender=contract_owner)



def test_add_loan_wrong_sender(loans_core_contract, contract_owner, borrower, test_collaterals):
    with boa.reverts("msg.sender is not the loans addr"):
        loans_core_contract.addLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            sender=contract_owner
        )


def test_add_loan(loans_core_contract, loans_peripheral_contract, borrower, contract_owner, test_collaterals):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )

    assert loan_id == 0

    assert loans_core_contract.getLoanAmount(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanInterest(borrower, loan_id) == LOAN_INTEREST
    assert loans_core_contract.getLoanMaturity(borrower, loan_id) == MATURITY
    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == 0
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == 0
    assert not loans_core_contract.getLoanStarted(borrower, loan_id)
    assert len(loans_core_contract.getLoanCollaterals(borrower, loan_id)) == len(test_collaterals)
    assert loans_core_contract.getLoanCollaterals(borrower, loan_id) == test_collaterals

    loan = loans_core_contract.getPendingLoan(borrower, loan_id)
    assert loans_core_contract.getLoanAmount(borrower, loan_id) == loan[1]
    assert loans_core_contract.getLoanInterest(borrower, loan_id) == loan[2]
    assert loans_core_contract.getLoanMaturity(borrower, loan_id) == loan[3]
    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == loan[6]
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == loan[7]
    assert loans_core_contract.getLoanStarted(borrower, loan_id) == loan[8]
    assert loans_core_contract.getLoanInvalidated(borrower, loan_id) == loan[9]
    assert loans_core_contract.getLoanPaid(borrower, loan_id) == loan[10]
    assert loans_core_contract.getLoanDefaulted(borrower, loan_id) == loan[11]
    assert loans_core_contract.getLoanCanceled(borrower, loan_id) == loan[12]

    pending_loan_collaterals = loans_core_contract.getPendingLoan(borrower, loan_id)[5]
    assert len(pending_loan_collaterals) == len(test_collaterals)
    assert pending_loan_collaterals == test_collaterals


    assert loans_core_contract.borrowedAmount(borrower) == 0

    assert loans_core_contract.ongoingLoans(borrower) == 1


def test_update_paid_loan_wrong_sender(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    with boa.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updatePaidLoan(borrower, 0, sender=contract_owner)


def test_update_paid_loan(loans_core_contract, loans_peripheral_contract, erc721_contract, borrower, contract_owner, test_collaterals):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)

    loans_core_contract.updatePaidLoan(borrower, loan_id, sender=loans_peripheral_contract.address)
    assert loans_core_contract.getLoanPaid(borrower, loan_id) == loans_core_contract.getLoan(borrower, loan_id)[10]
    assert loans_core_contract.getLoanPaid(borrower, loan_id)

    assert loans_core_contract.borrowedAmount(borrower) == 0
    assert loans_core_contract.collectionsBorrowedAmount(erc721_contract) == 0

    assert loans_core_contract.ongoingLoans(borrower) == 0


def test_update_defaulted_loan_wrong_sender(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    with boa.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updateDefaultedLoan(borrower, 0, sender=contract_owner)


def test_update_defaulted_loan(loans_core_contract, loans_peripheral_contract, erc721_contract, borrower, contract_owner, test_collaterals):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)

    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)
    assert loans_core_contract.getLoanDefaulted(borrower, loan_id) == loans_core_contract.getLoan(borrower, loan_id)[11]
    assert loans_core_contract.getLoanDefaulted(borrower, loan_id)

    assert loans_core_contract.borrowedAmount(borrower) == 0
    assert loans_core_contract.collectionsBorrowedAmount(erc721_contract) == 0

    assert loans_core_contract.ongoingLoans(borrower) == 0


def test_update_loan_started_wrong_sender(
    loans_core_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )


    with boa.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updateLoanStarted(borrower, loan_id, sender=contract_owner)


def test_update_loan_started(
    loans_core_contract,
    loans_peripheral_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )


    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)

    assert loans_core_contract.getLoanAmount(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanInterest(borrower, loan_id) == LOAN_INTEREST
    assert loans_core_contract.getLoanMaturity(borrower, loan_id) == MATURITY
    assert loans_core_contract.getLoanStarted(borrower, loan_id)
    assert len(loans_core_contract.getLoanCollaterals(borrower, loan_id)) == len(test_collaterals)
    assert loans_core_contract.getLoanCollaterals(borrower, loan_id) == test_collaterals

    assert loans_core_contract.borrowedAmount(borrower) == LOAN_AMOUNT
    assert loans_core_contract.collectionsBorrowedAmount(erc721_contract) == LOAN_AMOUNT


def test_update_paid_amount_wrong_sender(
    loans_core_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)

    with boa.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT, 0, sender=contract_owner)


def test_update_paid_amount(
    loans_core_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )


    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)

    loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT, 0, sender=loans_peripheral_contract.address)

    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == 0


def test_update_paid_amount_multiple(
    loans_core_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        sender=loans_peripheral_contract.address
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)

    loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT // 2, 0, sender=loans_peripheral_contract.address)

    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT // 2

    loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT // 2, 0, sender=loans_peripheral_contract.address)

    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == 0
