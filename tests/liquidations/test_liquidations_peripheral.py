from decimal import Decimal
from datetime import datetime as dt
from web3 import Web3

import boa
import eth_abi

from ..conftest_base import ZERO_ADDRESS, get_last_event, get_events

GRACE_PERIOD_DURATION = 50
LENDER_PERIOD_DURATION = 50
AUCTION_DURATION = 50

MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.to_wei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


def test_add_loans_core_address(liquidations_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract)
    event = get_last_event(liquidations_peripheral_contract, name="LoansCoreAddressAdded")

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_core_contract.address
    assert event.erc20TokenContract == erc20_contract.address


def test_add_loans_core_address_same_address(liquidations_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract)

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract.address

    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract)


def test_remove_loans_core_address_not_found(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address not found"):
        liquidations_peripheral_contract.removeLoansCoreAddress(erc20_contract.address)


def test_remove_loans_core_address(liquidations_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract.address, loans_core_contract.address)

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract.address) == loans_core_contract.address

    liquidations_peripheral_contract.removeLoansCoreAddress(erc20_contract.address)
    event = get_last_event(liquidations_peripheral_contract, name="LoansCoreAddressRemoved")

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract.address) == ZERO_ADDRESS

    assert event.currentValue == loans_core_contract.address
    assert event.erc20TokenContract == erc20_contract.address


def test_add_lending_pool_peripheral_address(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract)
    event = get_last_event(liquidations_peripheral_contract, name="LendingPoolPeripheralAddressAdded")

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == lending_pool_peripheral_contract.address
    assert event.erc20TokenContract == erc20_contract.address


def test_add_lending_pool_peripheral_address_same_address(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract)

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract.address

    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract)


def test_remove_lending_pool_peripheral_address_not_found(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address not found"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract)


def test_remove_lending_pool_peripheral_address(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract)

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract.address

    liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract)
    event = get_last_event(liquidations_peripheral_contract, name="LendingPoolPeripheralAddressRemoved")

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == ZERO_ADDRESS

    assert event.currentValue == lending_pool_peripheral_contract.address
    assert event.erc20TokenContract == erc20_contract.address


def test_set_collateral_vault_address(liquidations_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)
    event = get_last_event(liquidations_peripheral_contract, name="CollateralVaultPeripheralAddressSet")

    assert liquidations_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral_contract.address


def test_set_collateral_vault_address_same_address(liquidations_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)

    assert liquidations_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract.address

    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)


def test_set_collateral_vault_address(liquidations_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)
    event = get_last_event(liquidations_peripheral_contract, name="CollateralVaultPeripheralAddressSet")

    assert liquidations_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral_contract.address


def test_set_collateral_vault_address_same_address(liquidations_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)

    assert liquidations_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract.address

    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)


def test_load_contract_config(contracts_config, cryptopunk_collaterals, usdc_contract):
    pass  # contracts_config fixture active from this point on


def test_initial_state(liquidations_peripheral_contract, liquidations_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert liquidations_peripheral_contract.owner() == contract_owner
    assert liquidations_peripheral_contract.liquidationsCoreAddress() == liquidations_core_contract.address
    assert liquidations_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION
    assert liquidations_peripheral_contract.lenderPeriodDuration() == LENDER_PERIOD_DURATION
    assert liquidations_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION


def test_propose_owner_wrong_sender(liquidations_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("address it the zero address"):
        liquidations_peripheral_contract.proposeOwner(ZERO_ADDRESS)


def test_propose_owner_same_owner(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        liquidations_peripheral_contract.proposeOwner(contract_owner)


def test_propose_owner(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower)
    event = get_last_event(liquidations_peripheral_contract, name="OwnerProposed")

    assert liquidations_peripheral_contract.owner() == contract_owner
    assert liquidations_peripheral_contract.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower)
    
    with boa.reverts("proposed owner addr is the same"):
        liquidations_peripheral_contract.proposeOwner(borrower)


def test_claim_ownership_wrong_sender(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower)

    with boa.reverts("msg.sender is not the proposed"):
        liquidations_peripheral_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower)

    liquidations_peripheral_contract.claimOwnership(sender=borrower)
    event = get_last_event(liquidations_peripheral_contract, name="OwnershipTransferred")

    assert liquidations_peripheral_contract.owner() == borrower
    assert liquidations_peripheral_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_grace_period_duration_wrong_sender(liquidations_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setGracePeriodDuration(0, sender=borrower)


def test_set_grace_period_duration_zero_value(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("duration is 0"):
        liquidations_peripheral_contract.setGracePeriodDuration(0)


def test_set_grace_period_duration(liquidations_peripheral_contract, contract_owner):
    assert liquidations_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION

    liquidations_peripheral_contract.setGracePeriodDuration(GRACE_PERIOD_DURATION + 1)
    event = get_last_event(liquidations_peripheral_contract, name="GracePeriodDurationChanged")

    assert liquidations_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION + 1

    assert event.currentValue == GRACE_PERIOD_DURATION
    assert event.newValue == GRACE_PERIOD_DURATION + 1


def test_set_grace_period_duration_same_value(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.setGracePeriodDuration(GRACE_PERIOD_DURATION)


def test_set_lenders_period_duration_wrong_sender(liquidations_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setLendersPeriodDuration(0, sender=borrower)


def test_set_lenders_period_duration_zero_value(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("duration is 0"):
        liquidations_peripheral_contract.setLendersPeriodDuration(0)


def test_set_lenders_period_duration(liquidations_peripheral_contract, contract_owner):
    assert liquidations_peripheral_contract.lenderPeriodDuration() == LENDER_PERIOD_DURATION

    liquidations_peripheral_contract.setLendersPeriodDuration(LENDER_PERIOD_DURATION + 1)
    event = get_last_event(liquidations_peripheral_contract, name="LendersPeriodDurationChanged")

    assert liquidations_peripheral_contract.lenderPeriodDuration() == LENDER_PERIOD_DURATION + 1

    assert event.currentValue == LENDER_PERIOD_DURATION
    assert event.newValue == LENDER_PERIOD_DURATION + 1


def test_set_lenders_period_duration_same_value(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.setLendersPeriodDuration(LENDER_PERIOD_DURATION)


def test_set_auction_period_duration_wrong_sender(liquidations_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setAuctionPeriodDuration(0, sender=borrower)


def test_set_auction_period_duration_zero_value(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("duration is 0"):
        liquidations_peripheral_contract.setAuctionPeriodDuration(0)


def test_set_auction_period_duration(liquidations_peripheral_contract, contract_owner):
    assert liquidations_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION

    liquidations_peripheral_contract.setAuctionPeriodDuration(AUCTION_DURATION + 1)
    event = get_last_event(liquidations_peripheral_contract, name="AuctionPeriodDurationChanged")

    assert liquidations_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION + 1

    assert event.currentValue == AUCTION_DURATION
    assert event.newValue == AUCTION_DURATION + 1


def test_set_auction_period_duration_same_value(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.setAuctionPeriodDuration(AUCTION_DURATION)


def test_set_liquidations_core_address_wrong_sender(liquidations_peripheral_contract, liquidations_core_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(liquidations_core_contract, sender=borrower)


def test_set_liquidations_core_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(ZERO_ADDRESS)


def test_set_liquidations_core_address_not_contract(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("address is not a contract"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(contract_owner)


def test_set_liquidations_core_address(liquidations_peripheral_contract, liquidations_core_contract, loans_core_contract, contract_owner):
    liquidations_peripheral_contract.setLiquidationsCoreAddress(loans_core_contract)
    event = get_last_event(liquidations_peripheral_contract, name="LiquidationsCoreAddressSet")

    assert liquidations_peripheral_contract.liquidationsCoreAddress() == loans_core_contract.address

    assert event.currentValue == liquidations_core_contract.address
    assert event.newValue == loans_core_contract.address


def test_set_liquidations_core_address_same_address(liquidations_peripheral_contract, liquidations_core_contract, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(liquidations_core_contract)


def test_add_loans_core_address_wrong_sender(liquidations_peripheral_contract, loans_core_contract, erc20_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, sender=borrower)


def test_add_loans_core_address_zero_address(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, ZERO_ADDRESS)


def test_add_loans_core_address_not_contract(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address is not a contract"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, contract_owner)


def test_remove_loans_core_address_wrong_sender(liquidations_peripheral_contract, erc20_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.removeLoansCoreAddress(erc20_contract, sender=borrower)


def test_remove_loans_core_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("erc20TokenAddr is the zero addr"):
        liquidations_peripheral_contract.removeLoansCoreAddress(ZERO_ADDRESS)


def test_remove_loans_core_address_not_contract(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("erc20TokenAddr is not a contract"):
        liquidations_peripheral_contract.removeLoansCoreAddress(contract_owner)


def test_add_lending_pool_peripheral_address_wrong_sender(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, sender=borrower)


def test_add_lending_pool_peripheral_address_zero_address(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, ZERO_ADDRESS)


def test_add_lending_pool_peripheral_address_not_contract(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with boa.reverts("address is not a contract"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, contract_owner)


def test_remove_lending_pool_peripheral_address_wrong_sender(liquidations_peripheral_contract, erc20_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, sender=borrower)


def test_remove_lending_pool_peripheral_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("erc20TokenAddr is the zero addr"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(ZERO_ADDRESS)


def test_remove_lending_pool_peripheral_address_not_contract(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("erc20TokenAddr is not a contract"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(contract_owner)


def test_set_collateral_vault_address_wrong_sender(liquidations_peripheral_contract, collateral_vault_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, sender=borrower)


def test_set_collateral_vault_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(ZERO_ADDRESS)


def test_add_liquidation(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)
    liquidations_peripheral_contract.addLiquidation(borrower, loan_id, erc20_contract.address)
    event = get_last_event(liquidations_peripheral_contract, name="LiquidationAdded")

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    loan = loans_core_contract.getLoan(borrower, loan_id)

    interest_amount = int(Decimal(loan[1]) * Decimal(loan[2] * Decimal(loan[3] - loan[4])) / Decimal(25920000000))

    apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

    liquidation_id_abi_encoded = eth_abi.encode(
        ["address", "uint256", "uint256"],
        [erc721_contract.address, 0, liquidation[3]]
    )
    liquidation_id = Web3.solidity_keccak(["bytes32"], [liquidation_id_abi_encoded]).hex()

    assert liquidation[0].hex() == liquidation_id[2:]
    assert liquidation[4] == liquidation[3] + GRACE_PERIOD_DURATION
    assert liquidation[5] == liquidation[3] + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION
    assert liquidation[6] == LOAN_AMOUNT
    assert liquidation[7] == interest_amount
    assert liquidation[8] == apr
    assert liquidation[11] == borrower
    assert liquidation[12] == loan_id
    assert liquidation[13] == loans_core_contract.address
    assert liquidation[14] == erc20_contract.address

    assert event.liquidationId.hex() == liquidation_id[2:]
    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event.erc20TokenContract == erc20_contract.address
    assert event.gracePeriodPrice == Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + int(min(0.025 * LOAN_AMOUNT, Web3.to_wei(0.2, "ether")))
    assert event.lenderPeriodPrice == Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + int(min(0.025 * LOAN_AMOUNT, Web3.to_wei(0.2, "ether")))
    assert event.gracePeriodMaturity == liquidation[3] + GRACE_PERIOD_DURATION
    assert event.lenderPeriodMaturity == liquidation[3] + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION
    assert event.loansCoreContract == loans_core_contract.address
    assert event.loanId == loan_id
    assert event.borrower == borrower

    assert liquidations_core_contract.isLoanLiquidated(borrower, loans_core_contract, loan_id)


def test_add_liquidation_loan_not_defaulted(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )

    with boa.reverts("loan is not defaulted"):
        liquidations_peripheral_contract.addLiquidation(
            borrower,
            loan_id,
            erc20_contract
        )


def test_pay_loan_liquidations_grace_period(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)
    erc721_contract.mint(collateral_vault_core_contract, 1)

    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value= LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT // 2), (erc721_contract.address, 1, LOAN_AMOUNT // 2)],
        sender=loans_peripheral_contract.address
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(borrower, loan_id, erc20_contract)

    liquidation1 = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)
    liquidation2 = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 1)

    liquidations_peripheral_contract.payLoanLiquidationsGracePeriod(
        loan_id,
        erc20_contract,
        sender=borrower, value=liquidation1[9] + liquidation2[9]
    )

    event_liquidation_removed1, event_liquidation_removed2 = get_events(liquidations_peripheral_contract, name="LiquidationRemoved")[-2:]
    event_nft_purchased1, event_nft_purchased2 = get_events(liquidations_peripheral_contract, name="NFTPurchased")[-2:]
    fund_receipt_events = get_events(liquidations_peripheral_contract, name="FundsReceipt")

    # LIQUIDATION 1
    assert event_liquidation_removed1.liquidationId == liquidation1[0]
    assert event_liquidation_removed1.collateralAddress == erc721_contract.address
    assert event_liquidation_removed1.tokenId == 0
    assert event_liquidation_removed1.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed1.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed1.loanId == loan_id
    assert event_liquidation_removed1.borrower == borrower

    assert event_nft_purchased1.liquidationId == liquidation1[0]
    assert event_nft_purchased1.collateralAddress == erc721_contract.address
    assert event_nft_purchased1.tokenId == 0
    assert event_nft_purchased1.amount == liquidation1[9]
    assert event_nft_purchased1.buyerAddress == borrower
    assert event_nft_purchased1.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased1.method == "GRACE_PERIOD"

    # LIQUIDATION 2
    assert event_liquidation_removed2.liquidationId == liquidation2[0]
    assert event_liquidation_removed2.collateralAddress == erc721_contract.address
    assert event_liquidation_removed2.tokenId == 1
    assert event_liquidation_removed2.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed2.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed2.loanId == loan_id
    assert event_liquidation_removed2.borrower == borrower

    assert event_nft_purchased2.liquidationId == liquidation2[0]
    assert event_nft_purchased2.collateralAddress == erc721_contract.address
    assert event_nft_purchased2.tokenId == 1
    assert event_nft_purchased2.amount == liquidation2[9]
    assert event_nft_purchased2.buyerAddress == borrower
    assert event_nft_purchased2.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased2.method == "GRACE_PERIOD"

    for event in fund_receipt_events:
        assert event.fundsOrigin == "liquidation_grace_period"

    assert liquidations_core_contract.isLoanLiquidated(borrower, loans_core_contract, loan_id)


def test_pay_loan_liquidations_grace_period_usdc(
    usdc_contracts_config,
    liquidations_peripheral_contract,
    liquidations_core_contract,
    usdc_loans_peripheral_contract,
    usdc_loans_core_contract,
    usdc_lending_pool_peripheral_contract,
    usdc_lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    usdc_contract,
    borrower,
    contract_owner
):
    loan_amount = 10**9  # 1000 USDC

    erc721_contract.mint(collateral_vault_core_contract, 0, sender=contract_owner)

    usdc_contract.approve(usdc_lending_pool_core_contract, 2*loan_amount, sender=contract_owner)
    usdc_lending_pool_peripheral_contract.deposit(2*loan_amount, sender=contract_owner)
    usdc_lending_pool_peripheral_contract.sendFunds(contract_owner, loan_amount, sender=usdc_loans_peripheral_contract.address)

    loan_id = usdc_loans_core_contract.addLoan(
        borrower,
        loan_amount,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, loan_amount)],
        sender=usdc_loans_peripheral_contract.address
    )

    usdc_loans_core_contract.updateLoanStarted(borrower, loan_id, sender=usdc_loans_peripheral_contract.address)
    usdc_loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=usdc_loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        usdc_contract
    )

    liquidation1 = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)

    usdc_contract.transfer(borrower, liquidation1[9], sender=contract_owner)
    usdc_contract.approve(usdc_lending_pool_core_contract, liquidation1[9], sender=borrower)


    liquidations_peripheral_contract.payLoanLiquidationsGracePeriod(
        loan_id,
        usdc_contract,
        sender=borrower
    )
    event_liquidation_removed = get_last_event(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    fund_receipt_events = get_events(liquidations_peripheral_contract, name="FundsReceipt")

    assert event_liquidation_removed.liquidationId == liquidation1[0]
    assert event_liquidation_removed.collateralAddress == erc721_contract.address
    assert event_liquidation_removed.tokenId == 0
    assert event_liquidation_removed.erc20TokenContract == usdc_contract.address
    assert event_liquidation_removed.loansCoreContract == usdc_loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_purchased.liquidationId == liquidation1[0]
    assert event_nft_purchased.collateralAddress == erc721_contract.address
    assert event_nft_purchased.tokenId == 0
    assert event_nft_purchased.amount == liquidation1[9]
    assert event_nft_purchased.buyerAddress == borrower
    assert event_nft_purchased.erc20TokenContract == usdc_contract.address
    assert event_nft_purchased.method == "GRACE_PERIOD"

    for event in fund_receipt_events:
        assert event.fundsOrigin == "liquidation_grace_period"

    assert liquidations_core_contract.isLoanLiquidated(borrower, usdc_loans_core_contract, loan_id)


def test_buy_nft_lender_period_grace_period(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)

    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value= LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        erc20_contract
    )

    with boa.reverts("liquidation in grace period"):
        liquidations_peripheral_contract.buyNFTLenderPeriod(
            erc721_contract.address,
            0,
            sender=borrower, value= LOAN_AMOUNT * 2
        )


def test_buy_nft_lender_period_past_period(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)
    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value= LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        erc20_contract
    )

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    with boa.reverts("liquidation out of lender period"):
        liquidations_peripheral_contract.buyNFTLenderPeriod(
            erc721_contract.address,
            0,
            sender=borrower
        )


def test_buy_nft_lender_period_not_lender(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        erc20_contract
    )

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + 1)

    with boa.reverts("msg.sender is not a lender"):
        liquidations_peripheral_contract.buyNFTLenderPeriod(
            erc721_contract.address,
            0,
            sender=borrower
        )


def test_buy_nft_lender_period(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    erc721_contract.mint(collateral_vault_core_contract, 0)
    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value= LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        erc20_contract
    )

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + 1)

    liquidation_id = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)[0]
    loan = loans_core_contract.getLoan(borrower, loan_id)

    interest_amount = int(Decimal(loan[1]) * Decimal(loan[2] * Decimal(loan[3] - loan[4])) / Decimal(25920000000))

    liquidation_price = int(Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + int(min(0.025 * LOAN_AMOUNT, Web3.to_wei(0.2, "ether"))))

    liquidations_peripheral_contract.buyNFTLenderPeriod(erc721_contract.address, 0, sender=contract_owner, value=liquidation_price)
    event_liquidation_removed = get_last_event(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    event_funds_receipt = get_last_event(liquidations_peripheral_contract, name="FundsReceipt")


    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)
    assert liquidation[1] == ZERO_ADDRESS
    assert liquidation[3] == 0
    assert liquidation[11] == ZERO_ADDRESS
    assert liquidation[14] == ZERO_ADDRESS

    assert event_liquidation_removed.liquidationId == liquidation_id
    assert event_liquidation_removed.collateralAddress == erc721_contract.address
    assert event_liquidation_removed.tokenId == 0
    assert event_liquidation_removed.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_purchased.liquidationId == liquidation_id
    assert event_nft_purchased.collateralAddress == erc721_contract.address
    assert event_nft_purchased.tokenId == 0
    assert event_nft_purchased.amount == liquidation_price
    assert event_nft_purchased.buyerAddress == contract_owner
    assert event_nft_purchased.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased.method == "LENDER_PERIOD"

    assert event_funds_receipt.fundsOrigin == "liquidation_lenders_period"

    assert liquidations_core_contract.isLoanLiquidated(borrower, loans_core_contract, loan_id)


def test_admin_withdrawal_wrong_sender(
    liquidations_peripheral_contract,
    erc721_contract,
    borrower,
    contract_owner
):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.adminWithdrawal(
            contract_owner,
            erc721_contract.address,
            0,
            sender=borrower
        )


# def test_admin_withdrawal(
#     liquidations_peripheral_contract,
#     liquidations_core_contract,
#     loans_peripheral_contract,
#     loans_core_contract,
#     lending_pool_peripheral_contract,
#     lending_pool_core_contract,
#     collateral_vault_peripheral_contract,
#     collateral_vault_core_contract,
#     liquidity_controls_contract,
#     erc721_contract,
#     erc20_contract,
#     borrower,
#     contract_owner
# ):
#     collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)
#     collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)
    
#     liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

#     liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract)
#     liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract)
#     liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract)

#     loans_core_contract.setLoansPeripheral(loans_peripheral_contract)

#     lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract)
#     lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)
#     lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract)
#     lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract)

#     erc721_contract.mint(collateral_vault_core_contract, 0)

#     erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2)
#     erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2)
#     lending_pool_peripheral_contract.depositEth(LOAN_AMOUNT * 2)
#     lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract)
    
#     tx_add_loan = loans_core_contract.addLoan(
#         borrower,
#         LOAN_AMOUNT,
#         LOAN_INTEREST,
#         MATURITY,
#         [(erc721_contract, 0, LOAN_AMOUNT)],
#         sender=loans_peripheral_contract
#     )
#     loan_id = tx_add_loan.return_value
#     loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract)
#     loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract)

#     liquidations_peripheral_contract.addLiquidation(
#         erc721_contract,
#         0,
#         borrower,
#         loan_id,
#         erc20_contract
#     )

#     chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + AUCTION_DURATION)

#     liquidation_id = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)["lid"]

#     tx = liquidations_peripheral_contract.adminWithdrawal(
#         contract_owner,
#         erc721_contract,
#         0,
#         sender=contract_owner
#     )

#     liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
#     assert liquidation["collateralAddress"] == ZERO_ADDRESS
#     assert liquidation["startTime"] == 0
#     assert liquidation["borrower"] == ZERO_ADDRESS
#     assert liquidation["erc20TokenContract"] == ZERO_ADDRESS

#     event_liquidation_removed = tx.events.LiquidationRemoved
#     assert event_liquidation_removed.liquidationId == liquidation_id
#     assert event_liquidation_removed.collateralAddress == erc721_contract
#     assert event_liquidation_removed.tokenId == 0
#     assert event_liquidation_removed.erc20TokenContract == erc20_contract
#     assert event_liquidation_removed.loansCoreContract == loans_core_contract
#     assert event_liquidation_removed.loanId == loan_id
#     assert event_liquidation_removed.borrower == borrower

#     event_admin_withdrawal = tx.events.AdminWithdrawal
#     assert event_admin_withdrawal.liquidationId == liquidation_id
#     assert event_admin_withdrawal.collateralAddress == erc721_contract
#     assert event_admin_withdrawal.tokenId == 0
#     assert event_admin_withdrawal.wallet == contract_owner


def _create_liquidation(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
    ):
    erc721_contract.mint(collateral_vault_core_contract, 0)
    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value= LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        erc20_contract
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)
    loan = loans_core_contract.getLoan(borrower, loan_id)

    return (liquidation, loan)


def test_admin_liquidation(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    (liquidation, loan) = _create_liquidation(
        liquidations_peripheral_contract,
        liquidations_core_contract,
        loans_peripheral_contract,
        loans_core_contract,
        lending_pool_peripheral_contract,
        lending_pool_core_contract,
        collateral_vault_peripheral_contract,
        collateral_vault_core_contract,
        liquidity_controls_contract,
        erc721_contract,
        erc20_contract,
        borrower,
        contract_owner
    )

    liquidation_id = liquidation[0]
    collateral_address = liquidation[1]
    token_id = liquidation[2]
    loan_id = loan[0]
    investedAmount = liquidation[6]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)
    liquidations_peripheral_contract.adminWithdrawal(contract_owner, collateral_address, token_id)

    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT)
    liquidations_peripheral_contract.adminLiquidation(
        LOAN_AMOUNT*7//10,
        LOAN_AMOUNT*1//10,
        investedAmount,
        liquidation_id,
        liquidation[14],
        collateral_address,
        token_id,
        sender=contract_owner
    )
    liquidation_removed_events = get_events(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    event_funds_receipt = get_last_event(liquidations_peripheral_contract, name="FundsReceipt")

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)
    assert int(liquidation[0].hex()) == 0
    assert liquidation[1] == ZERO_ADDRESS
    assert liquidation[3] == 0
    assert liquidation[11] == ZERO_ADDRESS
    assert liquidation[14] == ZERO_ADDRESS

    assert not liquidation_removed_events

    assert event_nft_purchased.liquidationId == liquidation_id
    assert event_nft_purchased.collateralAddress == erc721_contract.address
    assert event_nft_purchased.tokenId == 0
    assert event_nft_purchased.amount == LOAN_AMOUNT * 8 // 10
    assert event_nft_purchased.buyerAddress == contract_owner
    assert event_nft_purchased.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased.method == "BACKSTOP_PERIOD_ADMIN"

    assert event_funds_receipt.fundsOrigin == "admin_liquidation"
    assert event_funds_receipt.investedAmount == investedAmount


def test_admin_liquidation_fail_on_message_not_from_owner(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    (liquidation, loan) = _create_liquidation(
        liquidations_peripheral_contract,
        liquidations_core_contract,
        loans_peripheral_contract,
        loans_core_contract,
        lending_pool_peripheral_contract,
        lending_pool_core_contract,
        collateral_vault_peripheral_contract,
        collateral_vault_core_contract,
        liquidity_controls_contract,
        erc721_contract,
        erc20_contract,
        borrower,
        contract_owner
    )

    collateral_address = liquidation[1]
    token_id = liquidation[2]
    liquidation_id = liquidation[0]

    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.adminLiquidation(
            LOAN_AMOUNT*7//10,
            LOAN_AMOUNT*1//10,
            liquidation[6],
            liquidation_id,
            liquidation[14],
            collateral_address,
            token_id,
            sender=borrower
        )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)
    assert liquidation[0] != ZERO_ADDRESS


def test_admin_liquidation_fail_on_collateral_in_vault(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    (liquidation, loan) = _create_liquidation(
        liquidations_peripheral_contract,
        liquidations_core_contract,
        loans_peripheral_contract,
        loans_core_contract,
        lending_pool_peripheral_contract,
        lending_pool_core_contract,
        collateral_vault_peripheral_contract,
        collateral_vault_core_contract,
        liquidity_controls_contract,
        erc721_contract,
        erc20_contract,
        borrower,
        contract_owner
    )

    collateral_address = liquidation[1]
    token_id = liquidation[2]
    liquidation_id = liquidation[0]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    with boa.reverts("collateral still owned by vault"):
        liquidations_peripheral_contract.adminLiquidation(
            LOAN_AMOUNT*7//10,
            LOAN_AMOUNT*1//10,
            liquidation[6],
            liquidation_id,
            liquidation[14],
            collateral_address,
            token_id,
            sender=contract_owner
        )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract.address, 0)
    assert liquidation[0] != ZERO_ADDRESS


def test_admin_liquidation_fail_on_collateral_in_liquidation(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    (liquidation, loan) = _create_liquidation(
        liquidations_peripheral_contract,
        liquidations_core_contract,
        loans_peripheral_contract,
        loans_core_contract,
        lending_pool_peripheral_contract,
        lending_pool_core_contract,
        collateral_vault_peripheral_contract,
        collateral_vault_core_contract,
        liquidity_controls_contract,
        erc721_contract,
        erc20_contract,
        borrower,
        contract_owner
    )

    collateral_address = liquidation[1]
    token_id = liquidation[2]
    liquidation_id = liquidation[0]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION)
    collateral_vault_peripheral_contract.transferCollateralFromLiquidation(contract_owner, collateral_address, token_id, sender=liquidations_peripheral_contract.address)

    with boa.reverts("collateral still in liquidation"):
        liquidations_peripheral_contract.adminLiquidation(
            LOAN_AMOUNT*7//10,
            LOAN_AMOUNT*1//10,
            liquidation[6],
            liquidation_id,
            liquidation[14],
            collateral_address,
            token_id,
            sender=contract_owner
        )


def test_cryptopunks_nftx_buy(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    cryptopunks_vault_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    cryptopunks_market_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    punk_owner = cryptopunks_market_contract.punkIndexToAddress(0)
    cryptopunks_market_contract.transferPunk(cryptopunks_vault_core_contract, 0, sender=punk_owner)

    lending_pool_peripheral_contract.depositEth(sender=contract_owner, value= LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(cryptopunks_market_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        erc20_contract
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(cryptopunks_market_contract, 0)
    loan = loans_core_contract.getLoan(borrower, loan_id)

    liquidation_id = liquidation[0]
    collateral_address = liquidation[1]
    token_id = liquidation[2]
    loan_id = loan[0]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    liquidations_peripheral_contract.liquidateNFTX(collateral_address, token_id)
    event_liquidation_removed = get_last_event(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    event_funds_receipt = get_last_event(liquidations_peripheral_contract, name="FundsReceipt")

    assert event_liquidation_removed.liquidationId == liquidation_id
    assert event_liquidation_removed.collateralAddress == cryptopunks_market_contract.address
    assert event_liquidation_removed.tokenId == 0
    assert event_liquidation_removed.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_purchased.liquidationId == liquidation_id
    assert event_nft_purchased.collateralAddress == cryptopunks_market_contract.address
    assert event_nft_purchased.tokenId == 0
    assert event_nft_purchased.buyerAddress == liquidations_peripheral_contract.nftxMarketplaceZapAddress()
    assert event_nft_purchased.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased.method == "BACKSTOP_PERIOD_NFTX"

    assert event_funds_receipt.fundsOrigin == "liquidation_nftx"


def test_hashmasks_nftx_buy(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    hashmasks_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    token_id: int = 0

    current_owner = hashmasks_contract.ownerOf(token_id)
    hashmasks_contract.transferFrom(current_owner, borrower, token_id, sender=current_owner)

    hashmasks_contract.safeTransferFrom(borrower, collateral_vault_core_contract.address, token_id, sender=borrower)

    erc20_contract.approve(lending_pool_core_contract.address, LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(hashmasks_contract.address, token_id, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(borrower, loan_id, erc20_contract.address)

    liquidation = liquidations_peripheral_contract.getLiquidation(hashmasks_contract.address, token_id)
    loan = loans_core_contract.getLoan(borrower, loan_id)

    liquidation_id = liquidation[0]
    collateral_address = liquidation[1]
    token_id = liquidation[2]
    loan_id = loan[0]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    liquidations_peripheral_contract.liquidateNFTX(collateral_address, token_id)
    event_liquidation_removed = get_last_event(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    event_funds_receipt = get_last_event(liquidations_peripheral_contract, name="FundsReceipt")

    assert event_liquidation_removed.liquidationId == liquidation_id
    assert event_liquidation_removed.collateralAddress == hashmasks_contract.address
    assert event_liquidation_removed.tokenId == token_id
    assert event_liquidation_removed.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_purchased.liquidationId == liquidation_id
    assert event_nft_purchased.collateralAddress == hashmasks_contract.address
    assert event_nft_purchased.tokenId == token_id
    assert event_nft_purchased.buyerAddress == liquidations_peripheral_contract.nftxMarketplaceZapAddress()
    assert event_nft_purchased.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased.method == "BACKSTOP_PERIOD_NFTX"

    assert event_funds_receipt.fundsOrigin == "liquidation_nftx"


def test_hashmasks_nftx_buy_usdc(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    usdc_loans_peripheral_contract,
    usdc_loans_core_contract,
    usdc_lending_pool_peripheral_contract,
    usdc_lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    usdc_liquidity_controls_contract,
    hashmasks_contract,
    usdc_contract,
    borrower,
    contract_owner
):
    token_id: int = 1
    loan_amount = 10**9

    current_owner = hashmasks_contract.ownerOf(token_id)
    hashmasks_contract.transferFrom(current_owner, borrower, token_id, sender=current_owner)

    hashmasks_contract.safeTransferFrom(borrower, collateral_vault_core_contract, token_id, sender=borrower)

    usdc_contract.approve(usdc_lending_pool_core_contract, loan_amount * 2, sender=contract_owner)
    usdc_lending_pool_peripheral_contract.deposit(loan_amount * 2, sender=contract_owner)
    usdc_lending_pool_peripheral_contract.sendFunds(contract_owner, loan_amount, sender=usdc_loans_peripheral_contract.address)

    loan_id = usdc_loans_core_contract.addLoan(
        borrower,
        loan_amount,
        LOAN_INTEREST,
        MATURITY,
        [(hashmasks_contract.address, token_id, loan_amount)],
        sender=usdc_loans_peripheral_contract.address
    )
    usdc_loans_core_contract.updateLoanStarted(borrower, loan_id, sender=usdc_loans_peripheral_contract.address)
    usdc_loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=usdc_loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(
        borrower,
        loan_id,
        usdc_contract
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(hashmasks_contract, token_id)
    loan = usdc_loans_core_contract.getLoan(borrower, loan_id)

    liquidation_id = liquidation[0]
    collateral_address = liquidation[1]
    token_id = liquidation[2]
    loan_id = loan[0]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    liquidations_peripheral_contract.liquidateNFTX(collateral_address, token_id, sender=contract_owner)
    event_liquidation_removed = get_last_event(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    event_funds_receipt = get_last_event(liquidations_peripheral_contract, name="FundsReceipt")

    assert event_liquidation_removed.liquidationId == liquidation_id
    assert event_liquidation_removed.collateralAddress == hashmasks_contract.address
    assert event_liquidation_removed.tokenId == token_id
    assert event_liquidation_removed.erc20TokenContract == usdc_contract.address
    assert event_liquidation_removed.loansCoreContract == usdc_loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_purchased.liquidationId == liquidation_id
    assert event_nft_purchased.collateralAddress == hashmasks_contract.address
    assert event_nft_purchased.tokenId == token_id
    assert event_nft_purchased.buyerAddress == liquidations_peripheral_contract.nftxMarketplaceZapAddress()
    assert event_nft_purchased.erc20TokenContract == usdc_contract.address
    assert event_nft_purchased.method == "BACKSTOP_PERIOD_NFTX"

    assert event_funds_receipt.fundsOrigin == "liquidation_nftx"


def test_wpunks_nftx_buy(
    liquidations_peripheral_contract,
    liquidations_core_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    cryptopunks_market_contract,
    wpunks_contract,
    erc20_contract,
    borrower,
    contract_owner
):
    token_id: int = 0

    wpunks_contract.registerProxy(sender=borrower)
    proxy = wpunks_contract.proxyInfo(borrower, sender=borrower)
    cryptopunks_market_contract.transferPunk(proxy, token_id, sender=borrower)
    wpunks_contract.mint(token_id, sender=borrower)

    wpunks_contract.safeTransferFrom(borrower, collateral_vault_core_contract, token_id, sender=borrower)

    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2)
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(wpunks_contract.address, token_id, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_peripheral_contract.addLiquidation(borrower, loan_id, erc20_contract)

    liquidation = liquidations_peripheral_contract.getLiquidation(wpunks_contract, token_id)
    loan = loans_core_contract.getLoan(borrower, loan_id)

    liquidation_id = liquidation[0]
    collateral_address = liquidation[1]
    token_id = liquidation[2]
    loan_id = loan[0]

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    liquidations_peripheral_contract.liquidateNFTX(collateral_address, token_id)
    event_liquidation_removed = get_last_event(liquidations_peripheral_contract, name="LiquidationRemoved")
    event_nft_purchased = get_last_event(liquidations_peripheral_contract, name="NFTPurchased")
    event_funds_receipt = get_last_event(liquidations_peripheral_contract, name="FundsReceipt")

    assert event_liquidation_removed.liquidationId == liquidation_id
    assert event_liquidation_removed.collateralAddress == wpunks_contract.address
    assert event_liquidation_removed.tokenId == token_id
    assert event_liquidation_removed.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_purchased.liquidationId == liquidation_id
    assert event_nft_purchased.collateralAddress == wpunks_contract.address
    assert event_nft_purchased.tokenId == token_id
    assert event_nft_purchased.buyerAddress == liquidations_peripheral_contract.nftxMarketplaceZapAddress()
    assert event_nft_purchased.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased.method == "BACKSTOP_PERIOD_NFTX"

    assert event_funds_receipt.fundsOrigin == "liquidation_nftx"


def test_store_collateral(
    collateral_vault_core_contract,
    collateral_vault_peripheral_contract,
    lending_pool_core_contract,
    lending_pool_peripheral_contract,
    liquidations_core_contract,
    liquidations_peripheral_contract,
    liquidity_controls_contract,
    loans_core_contract,
    loans_peripheral_contract,
    erc20_contract,
    erc721_contract,
    contract_owner
):
    _tokenId = 0
    erc721_contract.mint(liquidations_peripheral_contract, _tokenId)
    liquidations_peripheral_contract.storeERC721CollateralToVault(erc721_contract.address, _tokenId)
    assert erc721_contract.ownerOf(_tokenId) == collateral_vault_core_contract.address
