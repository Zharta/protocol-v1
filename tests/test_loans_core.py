import datetime as dt
import brownie

from web3 import Web3


MATURITY = int(dt.datetime.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


def test_initial_state(loans_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(loans_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(loans_core_contract, contract_owner):
    with brownie.reverts("_address it the zero address"):
        loans_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(loans_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        loans_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx = loans_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert loans_core_contract.proposedOwner() == borrower
    assert loans_core_contract.owner() == contract_owner

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        loans_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        loans_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = loans_core_contract.claimOwnership({"from": borrower})

    assert loans_core_contract.owner() == borrower
    assert loans_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_loans_peripheral_wrong_sender(loans_core_contract, loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": borrower})


def test_set_loans_peripheral_zero_address(loans_core_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_core_contract.setLoansPeripheral(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_loans_peripheral_same_address(loans_core_contract, loans_peripheral_contract, contract_owner):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts("new loans addr is the same"):
        loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})


def test_set_loans_peripheral(loans_core_contract, loans_peripheral_contract, contract_owner):
    tx = loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    assert loans_core_contract.loansPeripheral() == loans_peripheral_contract

    event = tx.events["LoansPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_peripheral_contract


def test_add_loan_wrong_sender(loans_core_contract, contract_owner, borrower, test_collaterals):
    with brownie.reverts("msg.sender is not the loans addr"):
        loans_core_contract.addLoan(
            borrower,
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {"from": contract_owner}
        )


def test_add_loan(loans_core_contract, loans_peripheral_contract, borrower, contract_owner, test_collaterals):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )

    loan_id = tx_add_loan.return_value
    assert loan_id == 0

    assert loans_core_contract.getLoanAmount(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanInterest(borrower, loan_id) == LOAN_INTEREST
    assert loans_core_contract.getLoanMaturity(borrower, loan_id) == MATURITY
    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == 0
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == 0
    assert not loans_core_contract.getLoanStarted(borrower, loan_id)
    assert len(loans_core_contract.getLoanCollaterals(borrower, loan_id)) == len(test_collaterals)
    assert loans_core_contract.getLoanCollaterals(borrower, loan_id) == test_collaterals

    assert loans_core_contract.getLoanAmount(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["amount"]
    assert loans_core_contract.getLoanInterest(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["interest"]
    assert loans_core_contract.getLoanMaturity(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["maturity"]
    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["paidPrincipal"]
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["paidInterestAmount"]
    assert loans_core_contract.getLoanStarted(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["started"]
    assert loans_core_contract.getLoanInvalidated(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["invalidated"]
    assert loans_core_contract.getLoanPaid(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["paid"]
    assert loans_core_contract.getLoanDefaulted(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["defaulted"]
    assert loans_core_contract.getLoanCanceled(borrower, loan_id) == loans_core_contract.getPendingLoan(borrower, loan_id)["canceled"]
    assert len(loans_core_contract.getPendingLoan(borrower, loan_id)["collaterals"]) == len(test_collaterals)
    assert loans_core_contract.getPendingLoan(borrower, loan_id)["collaterals"] == test_collaterals

    assert loans_core_contract.borrowedAmount(borrower) == 0

    assert loans_core_contract.ongoingLoans(borrower) == 1


def test_update_paid_loan_wrong_sender(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updatePaidLoan(borrower, 0, {"from": contract_owner})


def test_update_paid_loan(loans_core_contract, loans_peripheral_contract, erc721_contract, borrower, contract_owner, test_collaterals):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value

    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})

    loans_core_contract.updatePaidLoan(borrower, loan_id, {"from": loans_peripheral_contract})
    assert loans_core_contract.getLoanPaid(borrower, loan_id) == loans_core_contract.getLoan(borrower, loan_id)["paid"]
    assert loans_core_contract.getLoanPaid(borrower, loan_id)

    assert loans_core_contract.borrowedAmount(borrower) == 0
    assert loans_core_contract.collectionsBorrowedAmount(erc721_contract) == 0

    assert loans_core_contract.ongoingLoans(borrower) == 0


def test_update_defaulted_loan_wrong_sender(loans_core_contract, loans_peripheral_contract, contract_owner, borrower):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    
    with brownie.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updateDefaultedLoan(borrower, 0, {"from": contract_owner})


def test_update_defaulted_loan(loans_core_contract, loans_peripheral_contract, erc721_contract, borrower, contract_owner, test_collaterals):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value

    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})

    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})
    assert loans_core_contract.getLoanDefaulted(borrower, loan_id) == loans_core_contract.getLoan(borrower, loan_id)["defaulted"]
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
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )

    loan_id = tx_add_loan.return_value

    with brownie.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": contract_owner})


def test_update_loan_started(
    loans_core_contract,
    loans_peripheral_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )

    loan_id = tx_add_loan.return_value

    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})

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
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )

    loan_id = tx_add_loan.return_value

    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})

    with brownie.reverts("msg.sender is not the loans addr"):
        loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT, 0, {"from": contract_owner})


def test_update_paid_amount(
    loans_core_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )

    loan_id = tx_add_loan.return_value

    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})

    loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT, 0, {"from": loans_peripheral_contract})

    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == 0


def test_update_paid_amount_multiple(
    loans_core_contract,
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {"from": loans_peripheral_contract}
    )

    loan_id = tx_add_loan.return_value

    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})

    loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT / 2.0, 0, {"from": loans_peripheral_contract})

    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT / 2.0

    loans_core_contract.updateLoanPaidAmount(borrower, loan_id, LOAN_AMOUNT / 2.0, 0, {"from": loans_peripheral_contract})

    assert loans_core_contract.getLoanPaidPrincipal(borrower, loan_id) == LOAN_AMOUNT
    assert loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id) == 0
