import pytest
import datetime as dt
import brownie
import time

from brownie.network import chain
from decimal import Decimal
from web3 import Web3


MAX_NUMBER_OF_LOANS = 10
MAX_LOAN_DURATION = 31 * 24 * 60 * 60 # 31 days
MATURITY = int(dt.datetime.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000
MIN_LOAN_AMOUNT = Web3.toWei(0.05, "ether")
MAX_LOAN_AMOUNT = Web3.toWei(3, "ether")

PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000


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
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture
def erc20_contract(ERC20, contract_owner):
    yield ERC20.deploy("Wrapped ETH", "WETH", 18, 0, {'from': contract_owner})


@pytest.fixture
def erc721_contract(ERC721, contract_owner):
    yield ERC721.deploy({'from': contract_owner})


@pytest.fixture
def loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


@pytest.fixture
def lending_pool_core_contract(LendingPoolCore, erc20_contract, contract_owner):
    yield LendingPoolCore.deploy(
        erc20_contract,
        {'from': contract_owner}
    )


@pytest.fixture
def lending_pool_peripheral_contract(LendingPoolPeripheral, lending_pool_core_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolPeripheral.deploy(
        lending_pool_core_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture
def loans_contract(Loans, loans_core_contract, lending_pool_peripheral_contract, lending_pool_core_contract, contract_owner):
    yield Loans.deploy(
        MAX_NUMBER_OF_LOANS,
        MAX_LOAN_DURATION,
        MIN_LOAN_AMOUNT,
        MAX_LOAN_AMOUNT,
        loans_core_contract,
        lending_pool_peripheral_contract,
        lending_pool_core_contract,
        {'from': contract_owner}
    )


@pytest.fixture
def test_collaterals(erc721_contract):
    result = []
    for k in range(5):
        result.append((erc721_contract.address, k))
    yield result


def test_initial_state(loans_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_contract.owner() == contract_owner
    assert loans_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS
    assert loans_contract.minLoanAmount() == MIN_LOAN_AMOUNT
    assert loans_contract.maxLoanAmount() == MAX_LOAN_AMOUNT
    assert loans_contract.isAcceptingLoans() == True
    assert loans_contract.isDeprecated() == False


def test_propose_owner_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(loans_contract, contract_owner):
    with brownie.reverts("_address it the zero address"):
        loans_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(loans_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        loans_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(loans_contract, contract_owner, borrower):
    loans_contract.proposeOwner(borrower, {"from": contract_owner})

    assert loans_contract.proposedOwner() == borrower
    assert loans_contract.owner() == contract_owner


def test_propose_owner_same_proposed(loans_contract, contract_owner, borrower):
    loans_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        loans_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(loans_contract, contract_owner, borrower):
    loans_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        loans_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(loans_contract, contract_owner, borrower):
    loans_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = loans_contract.claimOwnership({"from": borrower})

    assert loans_contract.owner() == borrower
    assert loans_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_change_max_allowed_loans_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS - 1, {"from": borrower})


def test_change_max_allowed_loans(loans_contract, contract_owner):
    loans_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS - 1, {"from": contract_owner})
    assert loans_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS - 1

    loans_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS, {"from": contract_owner})
    assert loans_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS


def test_change_max_allowed_loan_duration_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION - 1, {"from": borrower})


def test_change_max_allowed_loan_duration(loans_contract, contract_owner):
    loans_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION - 1, {"from": contract_owner})
    assert loans_contract.maxAllowedLoanDuration() == MAX_LOAN_DURATION - 1

    loans_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION, {"from": contract_owner})
    assert loans_contract.maxAllowedLoanDuration() == MAX_LOAN_DURATION


def test_set_lending_pool_address_not_owner(loans_contract, lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.setLendingPoolPeripheralAddress(
            lending_pool_peripheral_contract,
            {"from": borrower}
        )


def test_set_lending_pool_address_zero_address(loans_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_contract.setLendingPoolPeripheralAddress(
            brownie.ZERO_ADDRESS,
            {"from": contract_owner}
        )


def test_set_lending_pool_address(loans_contract, lending_pool_peripheral_contract, contract_owner):
    loans_contract.setLendingPoolPeripheralAddress(
        contract_owner,
        {"from": contract_owner}
    )

    assert loans_contract.lendingPoolAddress() == contract_owner

    loans_contract.setLendingPoolPeripheralAddress(
        lending_pool_peripheral_contract,
        {"from": contract_owner}
    )

    assert loans_contract.lendingPoolAddress() == lending_pool_peripheral_contract


def test_add_address_to_whitelist_wrong_sender(loans_contract, erc721_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.addCollateralToWhitelist(
            erc721_contract,
            {"from": borrower}
        )


def test_add_address_to_whitelist_zero_address(loans_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_contract.addCollateralToWhitelist(
            brownie.ZERO_ADDRESS,
            {"from": contract_owner}
        )


def test_add_address_to_whitelist_not_contract_address(loans_contract, contract_owner):
    with brownie.reverts("_address is not a contract"):
        loans_contract.addCollateralToWhitelist(
            "0xa3aee8bce55beea1951ef834b99f3ac60d1abeeb",
            {"from": contract_owner}
        )


def test_add_address_to_whitelist_not_ERC721_contract(loans_contract, erc20_contract, contract_owner):
    with brownie.reverts(""):
        loans_contract.addCollateralToWhitelist(
            erc20_contract,
            {"from": contract_owner}
        )


def test_add_address_to_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(
        erc721_contract.address,
        {"from": contract_owner}
    )

    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == True


def test_remove_address_from_whitelist_wrong_sender(loans_contract, erc721_contract, contract_owner, borrower):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": borrower})


def test_remove_address_from_whitelist_not_whitelisted(loans_contract, erc721_contract, contract_owner):
    with brownie.reverts("collateral is not whitelisted"):
        loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})


def test_remove_address_from_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})
    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == True

    loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})
    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == False


def test_change_min_loan_amount_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.changeMinLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": borrower})


def test_change_min_loan_amount_wrong_amount(loans_contract, contract_owner):
    with brownie.reverts("min amount is > than max amount"):
        loans_contract.changeMinLoanAmount(MAX_LOAN_AMOUNT * 2, {"from": contract_owner})


def test_change_min_loan_amount(loans_contract, contract_owner):
    tx = loans_contract.changeMinLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": contract_owner})

    assert loans_contract.minLoanAmount() == MIN_LOAN_AMOUNT * 1.1


def test_change_max_loan_amount_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.changeMaxLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": borrower})


def test_change_max_loan_amount_wrong_amount(loans_contract, contract_owner):
    with brownie.reverts("max amount is < than min amount"):
        loans_contract.changeMaxLoanAmount(MIN_LOAN_AMOUNT / 2, {"from": contract_owner})


def test_change_max_loan_amount(loans_contract, contract_owner):
    tx = loans_contract.changeMaxLoanAmount(MAX_LOAN_AMOUNT * 1.1, {"from": contract_owner})

    assert loans_contract.maxLoanAmount() == MAX_LOAN_AMOUNT * 1.1


def test_change_contract_status_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.changeContractStatus(False, {"from": borrower})


def test_change_contract_status_same_status(loans_contract, contract_owner):
    with brownie.reverts("new contract status is the same"):
        loans_contract.changeContractStatus(True, {"from": contract_owner})


def test_change_contract_status(loans_contract, contract_owner):
    tx = loans_contract.changeContractStatus(False, {"from": contract_owner})

    assert loans_contract.isAcceptingLoans() == False


def test_deprecate_wrong_sender(loans_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.deprecate({"from": borrower})


def test_deprecate(loans_contract, contract_owner):
    tx = loans_contract.deprecate({"from": contract_owner})

    assert loans_contract.isDeprecated() == True
    assert loans_contract.isAcceptingLoans() == False


def test_deprecate_already_deprecated(loans_contract, contract_owner):
    loans_contract.deprecate({"from": contract_owner})

    with brownie.reverts("contract is already deprecated"):
        loans_contract.deprecate({"from": contract_owner})


def test_create_deprecated(
    loans_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_contract.deprecate({"from": contract_owner})

    with brownie.reverts("contract is deprecated"):
        tx_start_loan = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_not_accepting_loans(
    loans_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_contract.changeContractStatus(False, {"from": contract_owner})

    with brownie.reverts("contract is not accepting loans"):
        tx_start_loan = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_maturity_too_long(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    maturity = int(dt.datetime.now().timestamp()) + MAX_LOAN_DURATION * 2
    with brownie.reverts("maturity exceeds the max allowed"):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
            test_collaterals,
            {'from': borrower}
        )


def test_create_maturity_in_the_past(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    maturity = int(dt.datetime.now().timestamp()) - 3600
    with brownie.reverts("maturity is in the past"):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
            test_collaterals,
            {'from': borrower}
        )


def test_create_max_loans_reached(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(50, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(50, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(50, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(11):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    for k in range(MAX_NUMBER_OF_LOANS):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract.address, k)],
            {'from': borrower}
        )
        assert loans_contract.ongoingLoans(borrower) == k + 1
        time.sleep(0.2)

    with brownie.reverts("max loans already reached"):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract.address, MAX_NUMBER_OF_LOANS)],
            {'from': borrower}
        )


def test_create_collateral_notwhitelisted(
    loans_contract,
    loans_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    
    
    with brownie.reverts("not all NFTs are accepted"):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_collaterals_not_owned(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    erc721_contract.mint(investor, 0, {"from": contract_owner})

    with brownie.reverts("msg.sender does not own all NFTs"):
        tx = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_collateral_not_approved(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    with brownie.reverts("not all NFTs are approved"):
        tx = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_unsufficient_funds_in_lp(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    with brownie.reverts("insufficient liquidity"):
        tx = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_min_amount(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    with brownie.reverts("loan amount < than the min value"):
        tx = loans_contract.reserve(
            Web3.toWei(0.01, "ether"),
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_max_amount(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(15, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(15, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(15, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    with brownie.reverts("loan amount > than the max value"):
        tx = loans_contract.reserve(
            Web3.toWei(10, "ether"),
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loan_details = loans_contract.getPendingLoan(borrower, loan_id)
    assert loan_details["id"] == loan_id
    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["maturity"] == MATURITY
    assert len(loan_details["collaterals"]) == 5
    assert loan_details["collaterals"] == test_collaterals
    assert loan_details["started"] == False
    assert loan_details["invalidated"] == False
    assert loan_details["paid"] == False
    assert loan_details["defaulted"] == False
    assert loan_details["canceled"] == False

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address

    assert loans_contract.ongoingLoans(borrower) == 1

    assert tx_create_loan.events[-1]["wallet"] == borrower
    assert tx_create_loan.events[-1]["loanId"] == 0


def test_validate_wrong_sender(
    loans_contract,
    borrower
):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.validate(borrower, 0, {'from': borrower})


def test_validate_deprecated(
    loans_contract,
    contract_owner,
    borrower
):
    loans_contract.deprecate({"from": contract_owner})

    with brownie.reverts("contract is deprecated"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_not_accepting_loans(
    loans_contract,
    contract_owner,
    borrower
):
    loans_contract.changeContractStatus(False, {"from": contract_owner})

    with brownie.reverts("contract is not accepting loans"):
        tx_start_loan = loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan_not_created(
    loans_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("loan not found"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan_already_validated(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    print(loans_contract.getPendingLoan(borrower, loan_id))
    for collateral in test_collaterals:
        print(erc721_contract.ownerOf(collateral[1]))

    loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    
    print(loans_contract.getLoan(borrower, loan_id))
    print(loans_core_contract.getLoanStarted(borrower, loan_id))

    with brownie.reverts("loan already validated"):
        loans_contract.validate(borrower, loan_id, {'from': contract_owner})


def test_validate_loan_already_invalidated(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_contract.invalidate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already invalidated"):
        loans_contract.validate(borrower, loan_id, {'from': contract_owner})


def test_validate_maturity_in_the_past(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 3,
        test_collaterals,
        {'from': borrower}
    )

    assert tx_create_loan.return_value == 0

    time.sleep(5)
    with brownie.reverts("maturity is in the past"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_collateral_notwhitelisted(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("not all NFTs are accepted"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_unsufficient_funds_in_lp(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})   

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    lending_pool_peripheral_contract.withdraw(Web3.toWei(0.9, "ether"), {"from": investor})

    with brownie.reverts("insufficient liquidity"):
        tx = loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    
    loan_details = loans_contract.getLoan(borrower, loan_id)
    assert loan_details["id"] == loan_id
    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["maturity"] == MATURITY
    assert len(loan_details["collaterals"]) == 5
    assert loan_details["collaterals"] == test_collaterals
    assert loan_details["started"] == True
    assert loan_details["invalidated"] == False
    assert loan_details["paid"] == False
    assert loan_details["defaulted"] == False
    assert loan_details["canceled"] == False

    assert tx_start_loan.events[-1]["wallet"] == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address

    assert loans_core_contract.getHighestCollateralBundleLoan() == loan_details

    assert tx_start_loan.events["LoanValidated"]["wallet"] == borrower
    assert tx_start_loan.events["LoanValidated"]["loanId"] == 0


def test_invalidate_wrong_sender(
    loans_contract,
    borrower
):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.invalidate(borrower, 0, {'from': borrower})


def test_invalidate_loan_not_created(
    loans_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("loan not found"):
        loans_contract.invalidate(borrower, 0, {'from': contract_owner})


def test_invalidate_loan_already_invalidated(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_contract.invalidate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already invalidated"):
        loans_contract.invalidate(borrower, loan_id, {'from': contract_owner})


def test_invalidate_loan_already_validated(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already validated"):
        loans_contract.invalidate(borrower, loan_id, {'from': contract_owner})


def test_invalidate_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loan_details = loans_contract.getPendingLoan(borrower, loan_id)
    assert loan_details["id"] == loan_id
    assert loan_details["amount"] == LOAN_AMOUNT
    assert loan_details["interest"] == LOAN_INTEREST
    assert loan_details["paidAmount"] == 0
    assert loan_details["maturity"] == MATURITY
    assert len(loan_details["collaterals"]) == 5
    assert loan_details["collaterals"] == test_collaterals
    assert loan_details["started"] == False
    assert loan_details["invalidated"] == False
    assert loan_details["paid"] == False
    assert loan_details["defaulted"] == False
    assert loan_details["canceled"] == False

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address

    assert tx_create_loan.events[-1]["wallet"] == borrower
    assert tx_create_loan.events[-1]["loanId"] == 0

    tx_invalidate_loan = loans_contract.invalidate(borrower, 0, {'from': contract_owner})
    assert loans_contract.getLoan(borrower, loan_id)["invalidated"]

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert loans_contract.ongoingLoans(borrower) == 0

    assert tx_invalidate_loan.events[-1]["wallet"] == borrower
    assert tx_invalidate_loan.events[-1]["loanId"] == 0


def test_pay_loan_not_issued(loans_contract, borrower):
    with brownie.reverts("loan not found"):
        loans_contract.pay(0, LOAN_AMOUNT * (100 + LOAN_INTEREST) / 100, {"from": borrower})


def test_pay_loan_no_value_sent(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_contract.getLoan(borrower, loan_id)

    with brownie.reverts("_amount has to be higher than 0"):
        loans_contract.pay(loan["id"], 0, {"from": borrower})


def test_pay_loan_higher_value_than_needed(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_contract.getLoan(borrower, loan_id)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}") + 10000)

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    
    with brownie.reverts("_amount is more than needed"):
        loans_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_defaulted(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 5,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_contract.getLoan(borrower, loan_id)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    erc20_contract.mint(borrower, amount_paid, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})

    time.sleep(8)
    with brownie.reverts("loan maturity reached"):
        loans_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_insufficient_balance(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, (amount_paid - LOAN_AMOUNT) / 2, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    
    with brownie.reverts("insufficient balance"):
        tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan_insufficient_allowance(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_core_contract, amount_paid / 2, {"from": borrower})
    
    with brownie.reverts("insufficient allowance"):
        tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    loan_details = loans_contract.getLoan(borrower, loan_id)
    assert loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid
    assert loan_details["paid"] == loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loan_details["paidAmount"] == loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid

    assert tx_pay_loan.events["LoanPaid"]["wallet"] == borrower
    assert tx_pay_loan.events["LoanPaid"]["loanId"] == loan_id
    assert tx_pay_loan.events["LoanPayment"]["wallet"] == borrower
    assert tx_pay_loan.events["LoanPayment"]["loanId"] == loan_id
    assert tx_pay_loan.events["LoanPayment"]["amount"] == amount_paid

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert loans_contract.ongoingLoans(borrower) == 0

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - amount_paid


def test_pay_loan_multiple(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    amount_paid = int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    
    erc20_contract.mint(borrower, 2 * amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    tx_pay_loan1 = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    assert not loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address
    
    assert tx_pay_loan1.events["LoanPayment"]["wallet"] == borrower
    assert tx_pay_loan1.events["LoanPayment"]["loanId"] == loan_id
    assert tx_pay_loan1.events["LoanPayment"]["amount"] == amount_paid

    assert loans_contract.ongoingLoans(borrower) == 1

    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    tx_pay_loan2 = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    assert loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid * 2

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - amount_paid * 2

    assert loans_contract.ongoingLoans(borrower) == 0

    assert tx_pay_loan2.events["LoanPaid"]["wallet"] == borrower
    assert tx_pay_loan2.events["LoanPaid"]["loanId"] == loan_id
    assert tx_pay_loan2.events["LoanPayment"]["wallet"] == borrower
    assert tx_pay_loan2.events["LoanPayment"]["loanId"] == loan_id
    assert tx_pay_loan2.events["LoanPayment"]["amount"] == amount_paid


def test_set_default_loan_wrong_sender(
    loans_contract,
    investor,
    borrower
):
    with brownie.reverts("msg.sender is not the owner"):
        loans_contract.settleDefault(borrower, 0, {"from": investor})


def test_set_default_loan_not_started(
    loans_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("loan not found"):
        loans_contract.settleDefault(borrower, 0, {"from": contract_owner})


def test_set_default_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})    

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 5,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    time.sleep(8)
    loans_contract.settleDefault(borrower, loan_id, {"from": contract_owner})

    assert loans_core_contract.getLoanDefaulted(borrower, loan_id)

    assert loans_contract.ongoingLoans(borrower) == 0

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == contract_owner


def test_cancel_pendingloan_not_created(
    loans_contract,
    contract_owner
):
    with brownie.reverts("loan not found"):
        loans_contract.cancelPendingLoan(0, {"from": contract_owner})


def test_cancel_pendingloan_already_started(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    assert loans_contract.ongoingLoans(borrower) == 1

    loan_id = tx_create_loan.return_value

    loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already validated"):
        loans_contract.cancelPendingLoan(loan_id, {"from": borrower})


def test_cancel_pendingloan_invalidated(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    assert loans_contract.ongoingLoans(borrower) == 1

    loan_id = tx_create_loan.return_value

    loans_contract.invalidate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already invalidated"):
        loans_contract.cancelPendingLoan(loan_id, {"from": borrower})


def test_cancel_pending(
    loans_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    assert loans_contract.ongoingLoans(borrower) == 1

    loan_id = tx_create_loan.return_value

    tx_cancel_loan = loans_contract.cancelPendingLoan(loan_id, {"from": borrower})

    assert loans_core_contract.getLoanCanceled(borrower, loan_id)

    assert loans_contract.ongoingLoans(borrower) == 0

    assert tx_cancel_loan.events[-1]["wallet"] == borrower
    assert tx_cancel_loan.events[-1]["loanId"] == loan_id
