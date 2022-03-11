import pytest
import datetime as dt
import brownie
import time

from brownie.network import chain
from decimal import Decimal
from web3 import Web3



MAX_NUMBER_OF_LOANS = 10
MAX_LOAN_DURATION = 31 * 24 * 60 * 60 # 31 days
BUFFER_TO_CANCEL_LOAN = 3 # 3 seconds for testing purposes
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
def erc20_contract(ERC20PresetMinterPauser, contract_owner):
    yield ERC20PresetMinterPauser.deploy("Wrapped ETH", "WETH", {'from': contract_owner})


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
    yield Loans.deploy(
        MAX_NUMBER_OF_LOANS,
        MAX_LOAN_DURATION,
        BUFFER_TO_CANCEL_LOAN,
        MIN_LOAN_AMOUNT,
        MAX_LOAN_AMOUNT,
        {'from': contract_owner}
    )


@pytest.fixture
def loans_core_contract(LoansCore, loans_contract, contract_owner):
    yield LoansCore.deploy(
        loans_contract,
        MAX_NUMBER_OF_LOANS,
        {'from': contract_owner}
    )


@pytest.fixture
def lending_pool_contract(LendingPool, loans_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPool.deploy(
        loans_contract.address,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {"from": contract_owner}
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
    assert loans_contract.bufferToCancelLoan() == BUFFER_TO_CANCEL_LOAN
    assert loans_contract.minLoanAmount() == MIN_LOAN_AMOUNT
    assert loans_contract.maxLoanAmount() == MAX_LOAN_AMOUNT
    assert loans_contract.isAcceptingLoans() == True
    assert loans_contract.isDeprecated() == False


def test_change_ownership_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the owner can change the contract ownership"):
        loans_contract.changeOwnership(borrower, {"from": borrower})


def test_change_ownership(loans_contract, borrower, contract_owner):
    loans_contract.changeOwnership(borrower, {"from": contract_owner})
    assert loans_contract.owner() == borrower

    loans_contract.changeOwnership(contract_owner, {"from": borrower})
    assert loans_contract.owner() == contract_owner


def test_change_max_allowed_loans_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the owner can change the max allowed loans per address"):
        loans_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS - 1, {"from": borrower})


def test_change_max_allowed_loans(loans_contract, contract_owner):
    loans_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS - 1, {"from": contract_owner})
    assert loans_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS - 1

    loans_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS, {"from": contract_owner})
    assert loans_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS


def test_change_max_allowed_loan_duration_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the owner can change the max allowed loan duration"):
        loans_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION - 1, {"from": borrower})


def test_change_max_allowed_loan_duration(loans_contract, contract_owner):
    loans_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION - 1, {"from": contract_owner})
    assert loans_contract.maxAllowedLoanDuration() == MAX_LOAN_DURATION - 1

    loans_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION, {"from": contract_owner})
    assert loans_contract.maxAllowedLoanDuration() == MAX_LOAN_DURATION


def test_set_loans_core_address_not_owner(loans_contract, loans_core_contract, borrower):
    with brownie.reverts("Only the contract owner can set the LoansCore address"):
        loans_contract.setLoansCoreAddress(
            loans_core_contract.address,
            {"from": borrower}
        )


def test_set_lending_pool_address(loans_contract, loans_core_contract, contract_owner):
    loans_contract.setLoansCoreAddress(
        loans_core_contract.address,
        {"from": borrower}
    )


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

    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == True


def test_remove_address_from_whitelist_wrong_sender(loans_contract, erc721_contract, contract_owner, borrower):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("Only the contract owner can add collateral addresses to the whitelist"):
        loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": borrower})


def test_remove_address_from_whitelist_not_whitelisted(loans_contract, erc721_contract, contract_owner):
    with brownie.reverts("The collateral is not whitelisted"):
        loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})


def test_remove_address_from_whitelist(loans_contract, erc721_contract, contract_owner):
    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})
    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == True

    loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})
    assert loans_contract.whitelistedCollaterals(erc721_contract.address) == False


def test_change_min_loan_amount_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the contract owner can change the min loan amount"):
        loans_contract.changeMinLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": borrower})


def test_change_min_loan_amount_wrong_amount(loans_contract, contract_owner):
    with brownie.reverts("The min loan amount can not be higher than the max loan amount"):
        loans_contract.changeMinLoanAmount(MAX_LOAN_AMOUNT * 2, {"from": contract_owner})


def test_change_min_loan_amount(loans_contract, contract_owner):
    tx = loans_contract.changeMinLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": contract_owner})

    assert loans_contract.minLoanAmount() == MIN_LOAN_AMOUNT * 1.1
    assert tx.return_value == loans_contract.minLoanAmount()


def test_change_max_loan_amount_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the contract owner can change the max loan amount"):
        loans_contract.changeMaxLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": borrower})


def test_change_max_loan_amount_wrong_amount(loans_contract, contract_owner):
    with brownie.reverts("The max loan amount can not be lower than the min loan amount"):
        loans_contract.changeMaxLoanAmount(MIN_LOAN_AMOUNT / 2, {"from": contract_owner})


def test_change_max_loan_amount(loans_contract, contract_owner):
    tx = loans_contract.changeMaxLoanAmount(MAX_LOAN_AMOUNT * 1.1, {"from": contract_owner})

    assert loans_contract.maxLoanAmount() == MAX_LOAN_AMOUNT * 1.1
    assert tx.return_value == loans_contract.maxLoanAmount()


def test_change_contract_status_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the contract owner can change the status of the contract"):
        loans_contract.changeContractStatus(False, {"from": borrower})


def test_change_contract_status_same_status(loans_contract, contract_owner):
    with brownie.reverts("The new contract status should be different than the current status"):
        loans_contract.changeContractStatus(True, {"from": contract_owner})


def test_change_contract_status(loans_contract, contract_owner):
    tx = loans_contract.changeContractStatus(False, {"from": contract_owner})

    assert loans_contract.isAcceptingLoans() == False
    assert tx.return_value == loans_contract.isAcceptingLoans()


def test_deprecate_wrong_sender(loans_contract, borrower):
    with brownie.reverts("Only the contract owner can deprecate the contract"):
        loans_contract.deprecate({"from": borrower})


def test_deprecate(loans_contract, contract_owner):
    tx = loans_contract.deprecate({"from": contract_owner})

    assert loans_contract.isDeprecated() == True
    assert loans_contract.isAcceptingLoans() == False
    assert tx.return_value == loans_contract.isDeprecated()


def test_deprecate_already_deprecated(loans_contract, contract_owner):
    loans_contract.deprecate({"from": contract_owner})

    with brownie.reverts("The contract is already deprecated"):
        loans_contract.deprecate({"from": contract_owner})


def test_create_deprecated(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_contract.deprecate({"from": contract_owner})

    with brownie.reverts("The contract is deprecated, no more loans can be created"):
        tx_start_loan = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_not_accepting_loans(
    loans_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_contract.changeContractStatus(False, {"from": contract_owner})

    with brownie.reverts("The contract is not accepting more loans right now"):
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
    with brownie.reverts("Maturity can not exceed the max allowed"):
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
    with brownie.reverts("Maturity can not be in the past"):
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
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    erc20_contract.mint(investor, Web3.toWei(50, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(50, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(50, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(lending_pool_contract.address, {"from": contract_owner})

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    for k in range(MAX_NUMBER_OF_LOANS):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract.address, k)],
            {'from': borrower}
        )
        time.sleep(0.2)

    with brownie.reverts("Max number of started loans already reached"):
        loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract.address, 10)],
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
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    
    with brownie.reverts("Not all collaterals are whitelisted"):
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
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    erc721_contract.mint(investor, {"from": contract_owner})

    with brownie.reverts("Not all collaterals are owned by the borrower"):
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
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    with brownie.reverts("Not all collaterals are approved to be transferred"):
        tx = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_unsufficient_funds_in_lp(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    with brownie.reverts("Insufficient funds in the lending pool"):
        tx = loans_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_min_amount(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    with brownie.reverts("Loan amount is less than the min loan amount"):
        tx = loans_contract.reserve(
            Web3.toWei(0.01, "ether"),
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_max_amount(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(15, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(15, "ether"), {"from": investor})
    lending_pool_contract.deposit(Web3.toWei(15, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    with brownie.reverts("Loan amount is more than the max loan amount"):
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
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    loans = loans_contract.getPendingBorrowerLoans(borrower)
    assert len(loans) == 1

    loan_details = loans[0]
    assert loan_details[0] == 0
    assert loan_details[1] == LOAN_AMOUNT
    assert loan_details[2] == LOAN_INTEREST
    assert loan_details[6] == 0
    assert loan_details[3] == MATURITY
    assert len(loan_details[5]) == 5
    assert loan_details[5] == test_collaterals
    assert loan_details[7] == False

    assert loans_core_contract.nextLoanId(borrower) == 1

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address

    assert tx_create_loan.events[-1]["borrower"] == borrower
    assert tx_create_loan.events[-1]["loanId"] == 0

    assert len(loans_contract.getBorrowerLoans(borrower)) == 0


def test_validate_wrong_sender(
    loans_contract,
    borrower
):
    with brownie.reverts("Only the contract owner can validate loans"):
        loans_contract.validate(borrower, 0, {'from': borrower})


def test_validate_deprecated(
    loans_contract,
    contract_owner,
    borrower
):
    loans_contract.deprecate({"from": contract_owner})

    with brownie.reverts("The contract is deprecated, please pay any outstanding loans"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_not_accepting_loans(
    loans_contract,
    contract_owner,
    borrower
):
    loans_contract.changeContractStatus(False, {"from": contract_owner})

    with brownie.reverts("The contract is not accepting more loans right now, please pay any outstanding loans"):
        tx_start_loan = loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan_not_created(
    loans_contract,
    loans_core_contract,
    contract_owner,
    borrower
):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    
    with brownie.reverts("This loan has not been created for the borrower"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_maturity_in_the_past(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
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
    with brownie.reverts("Maturity can not be in the past"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})

    assert loans_core_contract.nextLoanId(borrower) == 1


def test_validate_collateral_notwhitelisted(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    loans_contract.removeCollateralFromWhitelist(erc721_contract.address, {"from": contract_owner})

    with brownie.reverts("Not all collaterals are whitelisted"):
        loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_collaterals_not_owned(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0)],
        {'from': borrower}
    )

    erc721_contract.transferFrom(loans_contract, borrower, 0, {"from": loans_contract})

    with brownie.reverts("Not all collaterals are owned by the protocol"):
        tx = loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_unsufficient_funds_in_lp(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    lending_pool_contract.withdraw(Web3.toWei(0.9, "ether"), {"from": investor})

    with brownie.reverts("Insufficient funds in the lending pool"):
        tx = loans_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    tx_start_loan = loans_contract.validate(borrower, 0, {'from': contract_owner})
    
    loans = loans_contract.getBorrowerLoans(borrower)
    assert len(loans) == 1

    loan_details = loans[0]

    assert loan_details[0] == 0
    assert loan_details[1] == LOAN_AMOUNT
    assert loan_details[2] == LOAN_INTEREST
    assert loan_details[6] == 0
    assert loan_details[3] == MATURITY
    assert len(loan_details[5]) == 5
    assert loan_details[5] == test_collaterals
    assert loan_details[7] == True

    assert loans_contract.currentStartedLoans() == 1
    assert loans_contract.totalStartedLoans() == 1

    assert loans_core_contract.nextLoanId(borrower) == 1

    assert tx_start_loan.events[-1]["borrower"] == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address

    assert loans_core_contract.getHighestCollateralBundleLoan() == loan_details


def test_invalidate_wrong_sender(
    loans_contract,
    borrower
):
    with brownie.reverts("Only the contract owner can invalidate loans"):
        loans_contract.invalidate(borrower, 0, {'from': borrower})


def test_invalidate_loan_not_created(
    loans_contract,
    loans_core_contract,
    contract_owner,
    borrower
):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})

    with brownie.reverts("This loan has not been created for the borrower"):
        loans_contract.invalidate(borrower, 0, {'from': contract_owner})


def test_invalidate_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    loans_contract.setLendingPoolAddress(
        lending_pool_contract.address,
        {"from": contract_owner}
    )

    loans_contract.addCollateralToWhitelist(erc721_contract.address, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.mint(borrower, {"from": contract_owner})
    erc721_contract.setApprovalForAll(loans_contract.address, True, {"from": borrower})

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    loan_details = loans_contract.getPendingBorrowerLoans(borrower)[0]
    assert loan_details[0] == 0
    assert loan_details[1] == LOAN_AMOUNT
    assert loan_details[2] == LOAN_INTEREST
    assert loan_details[6] == 0
    assert loan_details[3] == MATURITY
    assert len(loan_details[5]) == 5
    assert loan_details[5] == test_collaterals
    assert loan_details[7] == False

    assert loans_core_contract.nextLoanId(borrower) == 1

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address

    assert tx_create_loan.events[-1]["borrower"] == borrower
    assert tx_create_loan.events[-1]["loanId"] == 0

    tx_invalidate_loan = loans_contract.invalidate(borrower, 0, {'from': contract_owner})
    
    assert len(loans_contract.getBorrowerLoans(borrower)) == 0
    assert loans_core_contract.nextLoanId(borrower) == 0

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert tx_invalidate_loan.events[-1]["borrower"] == borrower
    assert tx_invalidate_loan.events[-1]["loanId"] == 0


def test_pay_loan_not_issued(loans_contract, loans_core_contract, contract_owner, borrower):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})

    with brownie.reverts("The sender has not started a loan with the given ID"):
        loans_contract.pay(0, LOAN_AMOUNT * (100 + LOAN_INTEREST) / 100, {"from": borrower})


def test_pay_loan_no_value_sent(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract.address, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_contract.getBorrowerLoan(borrower, loan_id)

    with brownie.reverts("The amount paid needs to be higher than 0"):
        loans_contract.pay(loan["id"], 0, {"from": borrower})


def test_pay_loan_higher_value_than_needed(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract.address, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_contract.getBorrowerLoan(borrower, loan_id)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}") + 10000)
    
    with brownie.reverts("The amount paid is higher than the amount left to be paid"):
        loans_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_defaulted(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 3,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_contract.getBorrowerLoan(borrower, loan_id)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    erc20_contract.mint(borrower, amount_paid, {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})

    time.sleep(5)
    with brownie.reverts("The maturity of the loan has already been reached and it defaulted"):
        loans_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_insufficient_balance(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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
    
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    
    with brownie.reverts("User has insufficient balance for the payment"):
        tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan_insufficient_allowance(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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
    
    erc20_contract.approve(lending_pool_contract, amount_paid / 2, {"from": borrower})
    
    with brownie.reverts("User did not allow funds to be transferred"):
        tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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
    
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    empty_loan = loans_contract.getBorrowerLoan(borrower, loan_id)
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    for collateral in empty_loan["collaterals"]:
        assert collateral["contractAddress"] == "0x0000000000000000000000000000000000000000"
        assert collateral["tokenId"] == 0

    assert loans_contract.currentStartedLoans() == 0
    assert loans_contract.totalPaidLoans() == 1

    assert tx_pay_loan.events[-1]["borrower"] == borrower

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - amount_paid


def test_pay_loan_multiple(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    loan_details = loans_contract.getBorrowerLoan(borrower, loan_id)
    assert loan_details["paidAmount"] == amount_paid
    assert loans_contract.currentStartedLoans() == 1
    assert loans_contract.totalPaidLoans() == 0

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == loans_contract.address
    
    erc20_contract.approve(lending_pool_contract, amount_paid, {"from": borrower})
    tx_pay_loan = loans_contract.pay(loan_id, amount_paid, {"from": borrower})

    empty_loan = loans_contract.getBorrowerLoan(borrower, loan_id)
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    for collateral in empty_loan["collaterals"]:
        assert collateral["contractAddress"] == "0x0000000000000000000000000000000000000000"
        assert collateral["tokenId"] == 0

    assert loans_contract.currentStartedLoans() == 0
    assert loans_contract.totalPaidLoans() == 1

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

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
    with brownie.reverts("Only the contract owner can default loans"):
        loans_contract.settleDefault(borrower, 0, {"from": investor})


def test_set_default_loan_not_started(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
    
    with brownie.reverts("The _borrower has not started a loan with the given ID"):
        loans_contract.settleDefault(borrower, 0, {"from": contract_owner})


def test_set_default_loan(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 3,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    time.sleep(5)
    loans_contract.settleDefault(borrower, loan_id, {"from": contract_owner})

    empty_loan = loans_contract.getBorrowerLoan(borrower, loan_id)
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    for collateral in empty_loan["collaterals"]:
        assert collateral["contractAddress"] == "0x0000000000000000000000000000000000000000"
        assert collateral["tokenId"] == 0

    assert loans_contract.currentStartedLoans() == 0
    assert loans_contract.totalStartedLoans() == 1
    assert loans_contract.totalDefaultedLoans() == 1

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == contract_owner


def test_cancel_pendingloan_not_created(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor
):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})

    with brownie.reverts("The sender has not created a loan with the given ID"):
        loans_contract.cancelPendingLoan(0, {"from": contract_owner})


def test_cancel_pending(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_cancel_loan = loans_contract.cancelPendingLoan(loan_id, {"from": borrower})

    empty_loan = loans_contract.getBorrowerLoan(borrower, loan_id)
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    for collateral in empty_loan["collaterals"]:
        assert collateral["contractAddress"] == "0x0000000000000000000000000000000000000000"
        assert collateral["tokenId"] == 0

    assert loans_core_contract.nextLoanId(borrower) == 0

    assert tx_cancel_loan.events[-1]["borrower"] == borrower
    assert tx_cancel_loan.events[-1]["loanId"] == loan_id


def test_cancel_approved_loan_not_started(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor
):
    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})

    with brownie.reverts("The sender has not started a loan with the given ID"):
        loans_contract.cancelStartedLoan(0, {"from": contract_owner})


def test_cancel_buffer_passed(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 3,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    time.sleep(5)
    with brownie.reverts("The time buffer to cancel the loan has passed"):
        loans_contract.cancelStartedLoan(loan_id, {"from": borrower})


def test_cancel(
    loans_contract,
    loans_core_contract,
    lending_pool_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_contract.deposit(Web3.toWei(1, "ether"), False, {"from": investor})

    loans_contract.setLoansCoreAddress(loans_core_contract, {"from": contract_owner})
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

    tx_create_loan = loans_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 5,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_contract.validate(borrower, loan_id, {'from': contract_owner})

    erc20_contract.mint(borrower, LOAN_AMOUNT, {"from": contract_owner})
    erc20_contract.approve(lending_pool_contract, LOAN_AMOUNT, {"from": borrower})
    tx_cancel_loan = loans_contract.cancelStartedLoan(loan_id, {"from": borrower})

    empty_loan = loans_contract.getBorrowerLoan(borrower, loan_id)
    assert empty_loan["amount"] == 0
    assert empty_loan["interest"] == 0
    assert empty_loan["paidAmount"] == 0

    for collateral in empty_loan["collaterals"]:
        assert collateral["contractAddress"] == "0x0000000000000000000000000000000000000000"
        assert collateral["tokenId"] == 0

    assert loans_contract.currentStartedLoans() == 0
    assert loans_contract.totalCanceledLoans() == 1

    assert tx_cancel_loan.events[-1]["borrower"] == borrower
    assert tx_cancel_loan.events[-1]["loanId"] == loan_id
