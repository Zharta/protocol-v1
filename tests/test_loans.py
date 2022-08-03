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

GRACE_PERIOD_DURATION = 5
LENDER_PERIOD_DURATION = 5
AUCTION_DURATION = 5


def test_initial_state(loans_peripheral_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_peripheral_contract.owner() == contract_owner
    assert loans_peripheral_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS
    assert loans_peripheral_contract.minLoanAmount() == MIN_LOAN_AMOUNT
    assert loans_peripheral_contract.maxLoanAmount() == MAX_LOAN_AMOUNT
    assert loans_peripheral_contract.isAcceptingLoans() == True
    assert loans_peripheral_contract.isDeprecated() == False


def test_propose_owner_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address it the zero address"):
        loans_peripheral_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(loans_peripheral_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        loans_peripheral_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(loans_peripheral_contract, contract_owner, borrower):
    tx = loans_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    assert loans_peripheral_contract.proposedOwner() == borrower
    assert loans_peripheral_contract.owner() == contract_owner

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        loans_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        loans_peripheral_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = loans_peripheral_contract.claimOwnership({"from": borrower})

    assert loans_peripheral_contract.owner() == borrower
    assert loans_peripheral_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_change_max_allowed_loans_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS - 1, {"from": borrower})


def test_change_max_allowed_loans(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS - 1, {"from": contract_owner})
    assert loans_peripheral_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS - 1

    event = tx.events["MaxLoansChanged"]
    assert event["currentValue"] == MAX_NUMBER_OF_LOANS
    assert event["newValue"] == MAX_NUMBER_OF_LOANS - 1

    tx = loans_peripheral_contract.changeMaxAllowedLoans(MAX_NUMBER_OF_LOANS, {"from": contract_owner})
    assert loans_peripheral_contract.maxAllowedLoans() == MAX_NUMBER_OF_LOANS

    event = tx.events["MaxLoansChanged"]
    assert event["currentValue"] == MAX_NUMBER_OF_LOANS - 1
    assert event["newValue"] == MAX_NUMBER_OF_LOANS


def test_change_max_allowed_loan_duration_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION - 1, {"from": borrower})


def test_change_max_allowed_loan_duration(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION - 1, {"from": contract_owner})
    assert loans_peripheral_contract.maxAllowedLoanDuration() == MAX_LOAN_DURATION - 1

    event = tx.events["MaxLoanDurationChanged"]
    assert event["currentValue"] == MAX_LOAN_DURATION
    assert event["newValue"] == MAX_LOAN_DURATION - 1

    tx = loans_peripheral_contract.changeMaxAllowedLoanDuration(MAX_LOAN_DURATION, {"from": contract_owner})
    assert loans_peripheral_contract.maxAllowedLoanDuration() == MAX_LOAN_DURATION

    event = tx.events["MaxLoanDurationChanged"]
    assert event["currentValue"] == MAX_LOAN_DURATION - 1
    assert event["newValue"] == MAX_LOAN_DURATION


def test_set_lending_pool_address_not_owner(loans_peripheral_contract, lending_pool_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.setLendingPoolPeripheralAddress(
            lending_pool_peripheral_contract,
            {"from": borrower}
        )


def test_set_lending_pool_address_zero_address(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_peripheral_contract.setLendingPoolPeripheralAddress(
            brownie.ZERO_ADDRESS,
            {"from": contract_owner}
        )


def test_set_lending_pool_address_not_contract(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address is not a contract"):
        loans_peripheral_contract.setLendingPoolPeripheralAddress(
            contract_owner,
            {"from": contract_owner}
        )


def test_set_lending_pool_address(loans_peripheral_contract, lending_pool_peripheral_contract, lending_pool_peripheral_contract_aux, contract_owner):
    tx = loans_peripheral_contract.setLendingPoolPeripheralAddress(
        lending_pool_peripheral_contract_aux,
        {"from": contract_owner}
    )

    assert loans_peripheral_contract.lendingPoolPeripheralAddress() == lending_pool_peripheral_contract_aux

    event = tx.events["LendingPoolPeripheralAddressSet"]
    assert event["currentValue"] == lending_pool_peripheral_contract
    assert event["newValue"] == lending_pool_peripheral_contract_aux

    tx = loans_peripheral_contract.setLendingPoolPeripheralAddress(
        lending_pool_peripheral_contract,
        {"from": contract_owner}
    )

    assert loans_peripheral_contract.lendingPoolPeripheralAddress() == lending_pool_peripheral_contract

    event = tx.events["LendingPoolPeripheralAddressSet"]
    assert event["currentValue"] == lending_pool_peripheral_contract_aux
    assert event["newValue"] == lending_pool_peripheral_contract


def test_add_address_to_whitelist_wrong_sender(loans_peripheral_contract, erc721_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.addCollateralToWhitelist(
            erc721_contract,
            {"from": borrower}
        )


def test_add_address_to_whitelist_zero_address(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_peripheral_contract.addCollateralToWhitelist(
            brownie.ZERO_ADDRESS,
            {"from": contract_owner}
        )


def test_add_address_to_whitelist_not_contract_address(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address is not a contract"):
        loans_peripheral_contract.addCollateralToWhitelist(
            "0xa3aee8bce55beea1951ef834b99f3ac60d1abeeb",
            {"from": contract_owner}
        )


def test_add_address_to_whitelist_not_ERC721_contract(loans_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts(""):
        loans_peripheral_contract.addCollateralToWhitelist(
            erc20_contract,
            {"from": contract_owner}
        )


def test_add_address_to_whitelist(loans_peripheral_contract, erc721_contract, contract_owner):
    tx = loans_peripheral_contract.addCollateralToWhitelist(
        erc721_contract,
        {"from": contract_owner}
    )

    assert loans_peripheral_contract.whitelistedCollaterals(erc721_contract)

    event = tx.events["CollateralToWhitelistAdded"]
    assert event["value"] == erc721_contract


def test_remove_address_from_whitelist_wrong_sender(loans_peripheral_contract, erc721_contract, contract_owner, borrower):
    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.removeCollateralFromWhitelist(erc721_contract, {"from": borrower})


def test_remove_address_from_whitelist_not_whitelisted(loans_peripheral_contract, erc721_contract, contract_owner):
    with brownie.reverts("collateral is not whitelisted"):
        loans_peripheral_contract.removeCollateralFromWhitelist(erc721_contract, {"from": contract_owner})


def test_remove_address_from_whitelist(loans_peripheral_contract, erc721_contract, contract_owner):
    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})
    assert loans_peripheral_contract.whitelistedCollaterals(erc721_contract)

    tx = loans_peripheral_contract.removeCollateralFromWhitelist(erc721_contract, {"from": contract_owner})
    assert not loans_peripheral_contract.whitelistedCollaterals(erc721_contract)

    event = tx.events["CollateralToWhitelistRemoved"]
    assert event["value"] == erc721_contract


def test_change_whitelist_status_wrong_sender(loans_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": investor})


def test_change_whitelist_status_same_status(loans_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        loans_peripheral_contract.changeWalletsWhitelistStatus(False, {"from": contract_owner})


def test_change_whitelist_status(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})
    assert loans_peripheral_contract.walletWhitelistEnabled()

    event = tx.events["WalletsWhitelistStatusChanged"]
    assert event["value"]

    tx = loans_peripheral_contract.changeWalletsWhitelistStatus(False, {"from": contract_owner})
    assert not loans_peripheral_contract.walletWhitelistEnabled()

    event = tx.events["WalletsWhitelistStatusChanged"]
    assert not event["value"]


def test_add_whitelisted_address_wrong_sender(loans_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.addWhitelistedWallet(investor, {"from": investor})


def test_add_whitelisted_address_zero_address(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_peripheral_contract.addWhitelistedWallet(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_whitelisted_address_whitelist_disabled(loans_peripheral_contract, contract_owner, investor):
    with brownie.reverts("wallets whitelist is disabled"):
        loans_peripheral_contract.addWhitelistedWallet(investor, {"from": contract_owner})


def test_add_whitelisted_address(loans_peripheral_contract, contract_owner, investor):
    loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})
    assert loans_peripheral_contract.walletWhitelistEnabled()

    tx = loans_peripheral_contract.addWhitelistedWallet(investor, {"from": contract_owner})
    assert loans_peripheral_contract.walletsWhitelisted(investor)

    event = tx.events["WhitelistedWalletAdded"]
    assert event["value"] == investor


def test_add_whitelisted_address_already_whitelisted(loans_peripheral_contract, contract_owner, investor):
    loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})
    assert loans_peripheral_contract.walletWhitelistEnabled()

    loans_peripheral_contract.addWhitelistedWallet(investor, {"from": contract_owner})
    assert loans_peripheral_contract.walletsWhitelisted(investor)

    with brownie.reverts("address is already whitelisted"):
        loans_peripheral_contract.addWhitelistedWallet(investor, {"from": contract_owner})


def test_remove_whitelisted_address_wrong_sender(loans_peripheral_contract, investor):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.removeWhitelistedWallet(investor, {"from": investor})


def test_remove_whitelisted_address_zero_address(loans_peripheral_contract, contract_owner):
    with brownie.reverts("_address is the zero address"):
        loans_peripheral_contract.removeWhitelistedWallet(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_whitelisted_address_whitelist_disabled(loans_peripheral_contract, contract_owner, investor):
    with brownie.reverts("wallets whitelist is disabled"):
        loans_peripheral_contract.removeWhitelistedWallet(investor, {"from": contract_owner})


def test_remove_whitelisted_address_not_whitelisted(loans_peripheral_contract, contract_owner, investor):
    loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})
    assert loans_peripheral_contract.walletWhitelistEnabled()

    with brownie.reverts("address is not whitelisted"):
        loans_peripheral_contract.removeWhitelistedWallet(investor, {"from": contract_owner})


def test_remove_whitelisted_address(loans_peripheral_contract, contract_owner, investor):
    loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})
    assert loans_peripheral_contract.walletWhitelistEnabled()

    loans_peripheral_contract.addWhitelistedWallet(investor, {"from": contract_owner})
    assert loans_peripheral_contract.walletsWhitelisted(investor)

    tx = loans_peripheral_contract.removeWhitelistedWallet(investor, {"from": contract_owner})
    assert not loans_peripheral_contract.walletsWhitelisted(investor)  

    event = tx.events["WhitelistedWalletRemoved"]
    assert event["value"] == investor


def test_change_min_loan_amount_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeMinLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": borrower})


def test_change_min_loan_amount_wrong_amount(loans_peripheral_contract, contract_owner):
    with brownie.reverts("min amount is > than max amount"):
        loans_peripheral_contract.changeMinLoanAmount(MAX_LOAN_AMOUNT * 2, {"from": contract_owner})


def test_change_min_loan_amount(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.changeMinLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": contract_owner})

    assert loans_peripheral_contract.minLoanAmount() == MIN_LOAN_AMOUNT * 1.1

    event = tx.events["MinLoanAmountChanged"]
    assert event["currentValue"] == MIN_LOAN_AMOUNT
    assert event["newValue"] == MIN_LOAN_AMOUNT * 1.1


def test_change_max_loan_amount_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeMaxLoanAmount(MIN_LOAN_AMOUNT * 1.1, {"from": borrower})


def test_change_max_loan_amount_wrong_amount(loans_peripheral_contract, contract_owner):
    with brownie.reverts("max amount is < than min amount"):
        loans_peripheral_contract.changeMaxLoanAmount(MIN_LOAN_AMOUNT / 2, {"from": contract_owner})


def test_change_max_loan_amount(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.changeMaxLoanAmount(MAX_LOAN_AMOUNT * 1.1, {"from": contract_owner})

    assert loans_peripheral_contract.maxLoanAmount() == MAX_LOAN_AMOUNT * 1.1

    event = tx.events["MaxLoanAmountChanged"]
    assert event["currentValue"] == MAX_LOAN_AMOUNT
    assert event["newValue"] == MAX_LOAN_AMOUNT * 1.1


def test_change_contract_status_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeContractStatus(False, {"from": borrower})


def test_change_contract_status_same_status(loans_peripheral_contract, contract_owner):
    with brownie.reverts("new contract status is the same"):
        loans_peripheral_contract.changeContractStatus(True, {"from": contract_owner})


def test_change_contract_status(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.changeContractStatus(False, {"from": contract_owner})

    assert not loans_peripheral_contract.isAcceptingLoans()

    event = tx.events["ContractStatusChanged"]
    assert not event["value"]


def test_deprecate_wrong_sender(loans_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.deprecate({"from": borrower})


def test_deprecate(loans_peripheral_contract, contract_owner):
    tx = loans_peripheral_contract.deprecate({"from": contract_owner})

    assert loans_peripheral_contract.isDeprecated() == True
    assert loans_peripheral_contract.isAcceptingLoans() == False

    event = tx.events["ContractDeprecated"]
    assert event is not None


def test_deprecate_already_deprecated(loans_peripheral_contract, contract_owner):
    loans_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("contract is already deprecated"):
        loans_peripheral_contract.deprecate({"from": contract_owner})


def test_create_deprecated(
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("contract is deprecated"):
        tx_start_loan = loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_not_accepting_loans(
    loans_peripheral_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_peripheral_contract.changeContractStatus(False, {"from": contract_owner})

    with brownie.reverts("contract is not accepting loans"):
        tx_start_loan = loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_maturity_too_long(
    loans_peripheral_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    maturity = int(dt.datetime.now().timestamp()) + MAX_LOAN_DURATION * 2
    with brownie.reverts("maturity exceeds the max allowed"):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
            test_collaterals,
            {'from': borrower}
        )


def test_create_maturity_in_the_past(
    loans_peripheral_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    maturity = int(dt.datetime.now().timestamp()) - 3600
    with brownie.reverts("maturity is in the past"):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
            test_collaterals,
            {'from': borrower}
        )


def test_create_max_loans_reached(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(50, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(50, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(50, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(11):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    for k in range(MAX_NUMBER_OF_LOANS):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract, k, LOAN_AMOUNT)],
            {'from': borrower}
        )
        assert loans_peripheral_contract.ongoingLoans(borrower) == k + 1
        time.sleep(0.2)

    with brownie.reverts("max loans already reached"):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract, MAX_NUMBER_OF_LOANS, LOAN_AMOUNT)],
            {'from': borrower}
        )


def test_create_collateral_notwhitelisted(
    loans_peripheral_contract,
    borrower,
    test_collaterals
):
    with brownie.reverts("not all NFTs are accepted"):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_collaterals_not_owned(
    loans_peripheral_contract,
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
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    erc721_contract.mint(investor, 0, {"from": contract_owner})

    with brownie.reverts("msg.sender does not own all NFTs"):
        tx = loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_collateral_not_approved(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    with brownie.reverts("not all NFTs are approved"):
        tx = loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_sum_collaterals_amounts_not_amount(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    with brownie.reverts("amount in collats != than amount"):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract, k, 0) for k in range(5)],
            {'from': borrower}
        )


def test_create_loan_unsufficient_funds_in_lp(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})

    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    with brownie.reverts("insufficient liquidity"):
        tx = loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan_min_amount(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})
    
    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    erc721_contract.mint(borrower, 0, {"from": contract_owner})

    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    with brownie.reverts("loan amount < than the min value"):
        loans_peripheral_contract.reserve(
            Web3.toWei(0.01, "ether"),
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract, 0, Web3.toWei(0.01, "ether"))],
            {'from': borrower}
        )


def test_create_loan_max_amount(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(15, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(15, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(15, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    erc721_contract.mint(borrower, 0, {"from": contract_owner})

    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    with brownie.reverts("loan amount > than the max value"):
        loans_peripheral_contract.reserve(
            Web3.toWei(10, "ether"),
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract, 0, Web3.toWei(10, "ether"))],
            {'from': borrower}
        )


def test_create_loan_wallet_not_whitelisted(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(15, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(15, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(15, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})

    with brownie.reverts("msg.sender is not whitelisted"):
        loans_peripheral_contract.reserve(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            {'from': borrower}
        )


def test_create_loan(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loan_details = loans_peripheral_contract.getPendingLoan(borrower, loan_id)
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
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract

    assert loans_peripheral_contract.ongoingLoans(borrower) == 1

    event = tx_create_loan.events["LoanCreated"]
    assert event["wallet"] == borrower
    assert event["loanId"] == 0


def test_create_loan_wallet_whitelist_enabled(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    loans_peripheral_contract.changeWalletsWhitelistStatus(True, {"from": contract_owner})
    loans_peripheral_contract.addWhitelistedWallet(borrower, {"from": contract_owner})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loan_details = loans_peripheral_contract.getPendingLoan(borrower, loan_id)
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
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract

    assert loans_peripheral_contract.ongoingLoans(borrower) == 1

    event = tx_create_loan.events["LoanCreated"]
    assert event["wallet"] == borrower
    assert event["loanId"] == 0


def test_validate_wrong_sender(
    loans_peripheral_contract,
    borrower
):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.validate(borrower, 0, {'from': borrower})


def test_validate_deprecated(
    loans_peripheral_contract,
    contract_owner,
    borrower
):
    loans_peripheral_contract.deprecate({"from": contract_owner})

    with brownie.reverts("contract is deprecated"):
        loans_peripheral_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_not_accepting_loans(
    loans_peripheral_contract,
    contract_owner,
    borrower
):
    loans_peripheral_contract.changeContractStatus(False, {"from": contract_owner})

    with brownie.reverts("contract is not accepting loans"):
        tx_start_loan = loans_peripheral_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan_not_created(
    loans_peripheral_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("loan not found"):
        loans_peripheral_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan_already_validated(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    print(loans_peripheral_contract.getPendingLoan(borrower, loan_id))
    for collateral in test_collaterals:
        print(erc721_contract.ownerOf(collateral[1]))

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})
    
    print(loans_peripheral_contract.getLoan(borrower, loan_id))
    print(loans_core_contract.getLoanStarted(borrower, loan_id))

    with brownie.reverts("loan already validated"):
        loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})


def test_validate_loan_already_invalidated(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.invalidate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already invalidated"):
        loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})


def test_validate_maturity_in_the_past(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 10,
        test_collaterals,
        {'from': borrower}
    )

    assert tx_create_loan.return_value == 0

    chain.mine(blocks=1, timedelta=15)
    #time.sleep(5)
    with brownie.reverts("maturity is in the past"):
        loans_peripheral_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_collateral_notwhitelisted(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    loans_peripheral_contract.removeCollateralFromWhitelist(erc721_contract, {"from": contract_owner})

    with brownie.reverts("not all NFTs are accepted"):
        loans_peripheral_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_unsufficient_funds_in_lp(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})   

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    lending_pool_peripheral_contract.withdraw(Web3.toWei(0.9, "ether"), {"from": investor})

    with brownie.reverts("insufficient liquidity"):
        tx = loans_peripheral_contract.validate(borrower, 0, {'from': contract_owner})


def test_validate_loan(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})
    
    loan_details = loans_peripheral_contract.getLoan(borrower, loan_id)
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
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract

    assert loans_core_contract.getHighestCollateralBundleLoan() == loan_details

    assert tx_start_loan.events["LoanValidated"]["wallet"] == borrower
    assert tx_start_loan.events["LoanValidated"]["loanId"] == 0

    assert loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id) == LOAN_AMOUNT

    chain.mine(blocks=1, timedelta=24 * 60 * 60)
    time_passed = (chain.time() - loan_details["startTime"]) - ((chain.time() - loan_details["startTime"]) % 86400)
    payable_amount = (Decimal(LOAN_AMOUNT) - Decimal(loan_details["paidAmount"])) * (Decimal(10000) * Decimal(MAX_LOAN_DURATION) + Decimal(LOAN_INTEREST) * Decimal(time_passed)) / (Decimal(10000) * Decimal(MAX_LOAN_DURATION))
    assert loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id) == payable_amount

    chain.mine(blocks=1, timedelta=12 * 60 * 60)
    assert loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id) == payable_amount


def test_invalidate_wrong_sender(
    loans_peripheral_contract,
    borrower
):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.invalidate(borrower, 0, {'from': borrower})


def test_invalidate_loan_not_created(
    loans_peripheral_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("loan not found"):
        loans_peripheral_contract.invalidate(borrower, 0, {'from': contract_owner})


def test_invalidate_loan_already_invalidated(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.invalidate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already invalidated"):
        loans_peripheral_contract.invalidate(borrower, loan_id, {'from': contract_owner})


def test_invalidate_loan_already_validated(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already validated"):
        loans_peripheral_contract.invalidate(borrower, loan_id, {'from': contract_owner})


def test_invalidate_loan(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loan_details = loans_peripheral_contract.getPendingLoan(borrower, loan_id)
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
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract

    assert tx_create_loan.events[-1]["wallet"] == borrower
    assert tx_create_loan.events[-1]["loanId"] == 0

    tx_invalidate_loan = loans_peripheral_contract.invalidate(borrower, 0, {'from': contract_owner})
    assert loans_peripheral_contract.getLoan(borrower, loan_id)["invalidated"]

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert loans_peripheral_contract.ongoingLoans(borrower) == 0

    assert tx_invalidate_loan.events[-1]["wallet"] == borrower
    assert tx_invalidate_loan.events[-1]["loanId"] == 0


def test_pay_loan_not_issued(loans_peripheral_contract, borrower):
    with brownie.reverts("loan not found"):
        loans_peripheral_contract.pay(0, LOAN_AMOUNT * (100 + LOAN_INTEREST) / 100, {"from": borrower})


def test_pay_loan_no_value_sent(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_peripheral_contract.getLoan(borrower, loan_id)

    with brownie.reverts("_amount has to be higher than 0"):
        loans_peripheral_contract.pay(loan["id"], 0, {"from": borrower})


def test_pay_loan_higher_value_than_needed(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_peripheral_contract.getLoan(borrower, loan_id)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    
    with brownie.reverts("_amount is more than needed"):
        loans_peripheral_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_defaulted(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 10,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})
    loan = loans_peripheral_contract.getLoan(borrower, loan_id)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    erc20_contract.mint(borrower, amount_paid, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})

    chain.mine(blocks=1, timedelta=15)
    with brownie.reverts("loan maturity reached"):
        loans_peripheral_contract.pay(loan["id"], amount_paid, {"from": borrower})


def test_pay_loan_insufficient_balance(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, (amount_paid - LOAN_AMOUNT) / 2, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_start_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    
    with brownie.reverts("insufficient balance"):
        tx_pay_loan = loans_peripheral_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan_insufficient_allowance(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)

    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT
    
    erc20_contract.approve(lending_pool_core_contract, amount_paid / 2, {"from": borrower})
    
    with brownie.reverts("insufficient allowance"):
        tx_pay_loan = loans_peripheral_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_pay_loan(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    tx_invest = lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    loan_details = loans_peripheral_contract.getLoan(borrower, loan_id)
    amount_payable = loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id)
    time_diff = chain.time() - loan_details['startTime'] - (chain.time() - loan_details['startTime']) % 86400
    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 * MAX_LOAN_DURATION + LOAN_INTEREST * time_diff) / (10000 * MAX_LOAN_DURATION)}"))
    assert amount_payable == amount_paid

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)
    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    
    tx_pay_loan = loans_peripheral_contract.pay(loan_id, amount_paid, {"from": borrower})

    loan_details = loans_peripheral_contract.getLoan(borrower, loan_id)
    assert loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid
    assert loan_details["paid"] == loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loan_details["paidAmount"] == loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid
    assert loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id) == 0

    assert tx_pay_loan.events["LoanPaid"]["wallet"] == borrower
    assert tx_pay_loan.events["LoanPaid"]["loanId"] == loan_id
    assert tx_pay_loan.events["LoanPayment"]["wallet"] == borrower
    assert tx_pay_loan.events["LoanPayment"]["loanId"] == loan_id
    assert tx_pay_loan.events["LoanPayment"]["amount"] == amount_paid

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert loans_peripheral_contract.ongoingLoans(borrower) == 0

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - amount_paid


def test_pay_loan_multiple(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    erc20_contract.mint(borrower, LOAN_AMOUNT * 2, {"from": contract_owner})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    borrower_initial_balance = erc20_contract.balanceOf(borrower)

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    loan_details = loans_peripheral_contract.getLoan(borrower, loan_id)
    time_diff = chain.time() - loan_details['startTime'] - (chain.time() - loan_details['startTime']) % 86400
    amount_paid = int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(10000 * MAX_LOAN_DURATION + LOAN_INTEREST * time_diff) / (10000 * MAX_LOAN_DURATION)}"))

    print(f"LOAN AMOUNT / 2 --> {LOAN_AMOUNT / 2.0}")
    print(f"TIME DIFF --> {time_diff}")
    print(f"AMOUNT PAID --> {amount_paid}")
    print(f"PAYABLE AMOUNT 1 --> {loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id)}")

    amount_payable = loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id)
    print(f"PAYABLE AMOUNT 2 --> {amount_payable}")
    assert amount_payable == amount_paid * 2

    borrower_amount_after_loan_started = erc20_contract.balanceOf(borrower)
    assert erc20_contract.balanceOf(borrower) == borrower_initial_balance + LOAN_AMOUNT

    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    tx_pay_loan1 = loans_peripheral_contract.pay(loan_id, amount_paid, {"from": borrower})

    assert not loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract
    
    assert tx_pay_loan1.events["LoanPayment"]["wallet"] == borrower
    assert tx_pay_loan1.events["LoanPayment"]["loanId"] == loan_id
    assert tx_pay_loan1.events["LoanPayment"]["amount"] == amount_paid

    assert loans_peripheral_contract.ongoingLoans(borrower) == 1

    time_diff = chain.time() - loan_details['startTime'] - (chain.time() - loan_details['startTime']) % 86400
    amount_paid2 = int(Decimal(f"{LOAN_AMOUNT / 2.0}") * Decimal(f"{(10000 * MAX_LOAN_DURATION + LOAN_INTEREST * time_diff) / (10000 * MAX_LOAN_DURATION)}"))
    
    erc20_contract.approve(lending_pool_core_contract, amount_paid2, {"from": borrower})
    tx_pay_loan2 = loans_peripheral_contract.pay(loan_id, amount_paid2, {"from": borrower})

    assert loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loans_core_contract.getLoanPaidAmount(borrower, loan_id) == amount_paid + amount_paid2
    assert loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id) == 0

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert erc20_contract.balanceOf(borrower) == borrower_amount_after_loan_started - (amount_paid + amount_paid2)

    assert loans_peripheral_contract.ongoingLoans(borrower) == 0

    assert tx_pay_loan2.events["LoanPaid"]["wallet"] == borrower
    assert tx_pay_loan2.events["LoanPaid"]["loanId"] == loan_id
    assert tx_pay_loan2.events["LoanPayment"]["wallet"] == borrower
    assert tx_pay_loan2.events["LoanPayment"]["loanId"] == loan_id
    assert tx_pay_loan2.events["LoanPayment"]["amount"] == amount_paid2


def test_pay_loan_already_paid(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    loan_details = loans_peripheral_contract.getLoan(borrower, loan_id)
    time_diff = chain.time() - loan_details['startTime'] - (chain.time() - loan_details['startTime']) % 86400
    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 * MAX_LOAN_DURATION + LOAN_INTEREST * time_diff) / (10000 * MAX_LOAN_DURATION)}"))

    erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, amount_paid, {"from": borrower})
    
    loans_peripheral_contract.pay(loan_id, amount_paid, {"from": borrower})

    with brownie.reverts("loan already paid"):
        loans_peripheral_contract.pay(loan_id, amount_paid, {"from": borrower})


def test_set_default_loan_wrong_sender(
    loans_peripheral_contract,
    investor,
    borrower
):
    with brownie.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.settleDefault(borrower, 0, {"from": investor})


def test_set_default_loan_not_started(
    loans_peripheral_contract,
    contract_owner,
    borrower
):
    with brownie.reverts("loan not found"):
        loans_peripheral_contract.settleDefault(borrower, 0, {"from": contract_owner})


def test_set_default_lender_zeroaddress(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})    

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        chain.time() + 10,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    tx_new_loan = loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    chain.mine(blocks=1, timedelta=15)
    
    with brownie.reverts("BNPeriph is the zero address"):
        loans_peripheral_contract.settleDefault(borrower, loan_id, {"from": contract_owner})


def test_set_default_loan(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidations_peripheral_contract,
    liquidations_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})    

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})
    loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    maturity = chain.time() + 10
    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        maturity,
        test_collaterals,
        {'from': borrower}
    )
    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    loan_start_time = loans_core_contract.getLoanStartTime(borrower, loan_id)

    chain.mine(blocks=1, timedelta=15)

    loans_peripheral_contract.settleDefault(borrower, loan_id, {"from": contract_owner})

    assert loans_core_contract.getLoanDefaulted(borrower, loan_id)

    assert loans_peripheral_contract.ongoingLoans(borrower) == 0

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract
        
        liquidation = liquidations_core_contract.getLiquidation(collateral[0], collateral[1])
        interest_amount = int(Decimal(collateral[2]) * Decimal(LOAN_INTEREST) / Decimal(10000))
        apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

        assert liquidation["collateralAddress"] == collateral[0]
        assert liquidation["tokenId"] == collateral[1]
        # assert liquidation["gracePeriodMaturity"] == default_time + GRACE_PERIOD_DURATION
        # assert liquidation["lenderPeriodMaturity"] == default_time + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION
        assert liquidation["principal"] == collateral[2]
        assert liquidation["interestAmount"] == interest_amount
        assert liquidation["apr"] == apr
        assert liquidation["gracePeriodPrice"] == int(Decimal(collateral[2]) + Decimal(interest_amount) + (Decimal(collateral[2]) * Decimal(apr) * Decimal(GRACE_PERIOD_DURATION)) / (Decimal(31536000) * Decimal(10000)))
        assert liquidation["lenderPeriodPrice"] == int(Decimal(collateral[2]) + Decimal(interest_amount) + (Decimal(collateral[2]) * Decimal(apr) * Decimal(LENDER_PERIOD_DURATION)) / (Decimal(31536000) * Decimal(10000)))
        assert liquidation["borrower"] == borrower
        assert liquidation["erc20TokenContract"] == erc20_contract
        assert not liquidation["inAuction"]


def test_cancel_pendingloan_not_created(
    loans_peripheral_contract,
    contract_owner
):
    with brownie.reverts("loan not found"):
        loans_peripheral_contract.cancelPendingLoan(0, {"from": contract_owner})


def test_cancel_pendingloan_already_started(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})

    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    assert loans_peripheral_contract.ongoingLoans(borrower) == 1

    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.validate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already validated"):
        loans_peripheral_contract.cancelPendingLoan(loan_id, {"from": borrower})


def test_cancel_pendingloan_invalidated(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    assert loans_peripheral_contract.ongoingLoans(borrower) == 1

    loan_id = tx_create_loan.return_value

    loans_peripheral_contract.invalidate(borrower, loan_id, {'from': contract_owner})

    with brownie.reverts("loan already invalidated"):
        loans_peripheral_contract.cancelPendingLoan(loan_id, {"from": borrower})


def test_cancel_pending(
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc20_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals
):
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})

    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    erc20_contract.mint(investor, Web3.toWei(1, "ether"), {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, Web3.toWei(1, "ether"), {"from": investor})
    
    lending_pool_peripheral_contract.deposit(Web3.toWei(1, "ether"), {"from": investor})

    loans_peripheral_contract.addCollateralToWhitelist(erc721_contract, {"from": contract_owner})

    for k in range(5):
        erc721_contract.mint(borrower, k, {"from": contract_owner})
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, {"from": borrower})

    tx_create_loan = loans_peripheral_contract.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        {'from': borrower}
    )

    assert loans_peripheral_contract.ongoingLoans(borrower) == 1

    loan_id = tx_create_loan.return_value

    tx_cancel_loan = loans_peripheral_contract.cancelPendingLoan(loan_id, {"from": borrower})

    assert loans_core_contract.getLoanCanceled(borrower, loan_id)

    assert loans_peripheral_contract.ongoingLoans(borrower) == 0

    assert tx_cancel_loan.events[-1]["wallet"] == borrower
    assert tx_cancel_loan.events[-1]["loanId"] == loan_id
