from decimal import Decimal
from brownie.network import chain
from datetime import datetime as dt
from web3 import Web3

import brownie
import eth_abi


GRACE_PERIOD_DURATION = 5
LENDER_PERIOD_DURATION = 5
AUCTION_DURATION = 5

MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


def test_initial_state(liquidations_peripheral_contract, liquidations_core_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert liquidations_peripheral_contract.owner() == contract_owner
    assert liquidations_peripheral_contract.liquidationsCoreAddress() == liquidations_core_contract
    assert liquidations_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION
    assert liquidations_peripheral_contract.lenderPeriodDuration() == LENDER_PERIOD_DURATION
    assert liquidations_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION


def test_propose_owner_wrong_sender(liquidations_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        liquidations_peripheral_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        liquidations_peripheral_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(liquidations_peripheral_contract, contract_owner, borrower):
    tx = liquidations_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    assert liquidations_peripheral_contract.owner() == contract_owner
    assert liquidations_peripheral_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        liquidations_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        liquidations_peripheral_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(liquidations_peripheral_contract, contract_owner, borrower):
    liquidations_peripheral_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = liquidations_peripheral_contract.claimOwnership({"from": borrower})

    assert liquidations_peripheral_contract.owner() == borrower
    assert liquidations_peripheral_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_grace_period_duration_wrong_sender(liquidations_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setGracePeriodDuration(0, {"from": borrower})


def test_set_grace_period_duration_zero_value(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("duration is 0"):
        liquidations_peripheral_contract.setGracePeriodDuration(0, {"from": contract_owner})


def test_set_grace_period_duration(liquidations_peripheral_contract, contract_owner):
    assert liquidations_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION
    
    tx = liquidations_peripheral_contract.setGracePeriodDuration(GRACE_PERIOD_DURATION + 1, {"from": contract_owner})

    assert liquidations_peripheral_contract.gracePeriodDuration() == GRACE_PERIOD_DURATION + 1

    event = tx.events["GracePeriodDurationChanged"]
    assert event["currentValue"] == GRACE_PERIOD_DURATION
    assert event["newValue"] == GRACE_PERIOD_DURATION + 1


def test_set_grace_period_duration_same_value(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.setGracePeriodDuration(GRACE_PERIOD_DURATION, {"from": contract_owner})


def test_set_lenders_period_duration_wrong_sender(liquidations_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setLendersPeriodDuration(0, {"from": borrower})


def test_set_lenders_period_duration_zero_value(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("duration is 0"):
        liquidations_peripheral_contract.setLendersPeriodDuration(0, {"from": contract_owner})


def test_set_lenders_period_duration(liquidations_peripheral_contract, contract_owner):
    assert liquidations_peripheral_contract.lenderPeriodDuration() == LENDER_PERIOD_DURATION
    
    tx = liquidations_peripheral_contract.setLendersPeriodDuration(LENDER_PERIOD_DURATION + 1, {"from": contract_owner})

    assert liquidations_peripheral_contract.lenderPeriodDuration() == LENDER_PERIOD_DURATION + 1

    event = tx.events["LendersPeriodDurationChanged"]
    assert event["currentValue"] == LENDER_PERIOD_DURATION
    assert event["newValue"] == LENDER_PERIOD_DURATION + 1


def test_set_lenders_period_duration_same_value(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.setLendersPeriodDuration(LENDER_PERIOD_DURATION, {"from": contract_owner})


def test_set_auction_period_duration_wrong_sender(liquidations_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setAuctionPeriodDuration(0, {"from": borrower})


def test_set_auction_period_duration_zero_value(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("duration is 0"):
        liquidations_peripheral_contract.setAuctionPeriodDuration(0, {"from": contract_owner})


def test_set_auction_period_duration(liquidations_peripheral_contract, contract_owner):
    assert liquidations_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION
    
    tx = liquidations_peripheral_contract.setAuctionPeriodDuration(AUCTION_DURATION + 1, {"from": contract_owner})

    assert liquidations_peripheral_contract.auctionPeriodDuration() == AUCTION_DURATION + 1

    event = tx.events["AuctionPeriodDurationChanged"]
    assert event["currentValue"] == AUCTION_DURATION
    assert event["newValue"] == AUCTION_DURATION + 1


def test_set_auction_period_duration_same_value(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.setAuctionPeriodDuration(AUCTION_DURATION, {"from": contract_owner})


def test_set_liquidations_core_address_wrong_sender(liquidations_peripheral_contract, liquidations_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(liquidations_core_contract, {"from": borrower})


def test_set_liquidations_core_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_liquidations_core_address_not_contract(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(contract_owner, {"from": contract_owner})


def test_set_liquidations_core_address(liquidations_peripheral_contract, liquidations_core_contract, loans_core_contract, contract_owner):
    tx = liquidations_peripheral_contract.setLiquidationsCoreAddress(loans_core_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.liquidationsCoreAddress() == loans_core_contract

    event = tx.events["LiquidationsCoreAddressSet"]
    assert event["currentValue"] == liquidations_core_contract
    assert event["newValue"] == loans_core_contract


def test_set_liquidations_core_address_same_address(liquidations_peripheral_contract, liquidations_core_contract, contract_owner):
    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.setLiquidationsCoreAddress(liquidations_core_contract, {"from": contract_owner})


def test_add_loans_core_address_wrong_sender(liquidations_peripheral_contract, loans_core_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": borrower})


def test_add_loans_core_address_zero_address(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_loans_core_address_not_contract(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_loans_core_address(liquidations_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    tx = liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    event = tx.events["LoansCoreAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_loans_core_address_same_address(liquidations_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})


def test_remove_loans_core_address_wrong_sender(liquidations_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.removeLoansCoreAddress(erc20_contract, {"from": borrower})


def test_remove_loans_core_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        liquidations_peripheral_contract.removeLoansCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_loans_core_address_not_contract(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        liquidations_peripheral_contract.removeLoansCoreAddress(contract_owner, {"from": contract_owner})


def test_remove_loans_core_address_not_found(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        liquidations_peripheral_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})


def test_remove_loans_core_address(liquidations_peripheral_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    tx = liquidations_peripheral_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.loansCoreAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LoansCoreAddressRemoved"]
    assert event["currentValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_lending_pool_peripheral_address_wrong_sender(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": borrower})


def test_add_lending_pool_peripheral_address_zero_address(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_lending_pool_peripheral_address_not_contract(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_lending_pool_peripheral_address(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    tx = liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract

    event = tx.events["LendingPoolPeripheralAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == lending_pool_peripheral_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_lending_pool_peripheral_address_same_address(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract

    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address_wrong_sender(liquidations_peripheral_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, {"from": borrower})


def test_remove_lending_pool_peripheral_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address_not_contract(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(contract_owner, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address_not_found(liquidations_peripheral_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, {"from": contract_owner})


def test_remove_lending_pool_peripheral_address(liquidations_peripheral_contract, lending_pool_peripheral_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == lending_pool_peripheral_contract

    tx = liquidations_peripheral_contract.removeLendingPoolPeripheralAddress(erc20_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.lendingPoolPeripheralAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LendingPoolPeripheralAddressRemoved"]
    assert event["currentValue"] == lending_pool_peripheral_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_set_collateral_vault_address_wrong_sender(liquidations_peripheral_contract, collateral_vault_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": borrower})


def test_set_collateral_vault_address_zero_address(liquidations_peripheral_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_collateral_vault_address(liquidations_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    tx = liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    event = tx.events["CollateralVaultPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == collateral_vault_peripheral_contract


def test_set_collateral_vault_address_same_address(liquidations_peripheral_contract, collateral_vault_peripheral_contract, contract_owner):
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    assert liquidations_peripheral_contract.collateralVaultPeripheralAddress() == collateral_vault_peripheral_contract

    with brownie.reverts("new value is the same"):
        liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})


def test_add_liquidation_collat_not_owned_by_vault(liquidations_peripheral_contract, liquidations_core_contract, collateral_vault_peripheral_contract, erc721_contract, contract_owner):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by vault"):
        liquidations_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            brownie.ZERO_ADDRESS,
            0,
            brownie.ZERO_ADDRESS
        )


def test_add_liquidation(liquidations_peripheral_contract, liquidations_core_contract, loans_peripheral_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    tx = liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    loan = loans_core_contract.getLoan(borrower, loan_id)

    interest_amount = int(Decimal(loan["amount"]) * Decimal(loan["interest"] * Decimal(loan["maturity"] - loan["startTime"])) / Decimal(25920000000))
    print(interest_amount)
    
    apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

    liquidation_id_abi_encoded = eth_abi.encode_abi(
        ["address", "uint256", "uint256"],
        [erc721_contract.address, 0, liquidation["startTime"]]
    ).hex()
    liquidation_id = Web3.solidityKeccak(
        ["bytes32"],
        ["0x" + liquidation_id_abi_encoded]
    ).hex()

    assert liquidation["lid"] == liquidation_id
    assert liquidation["gracePeriodMaturity"] == liquidation["startTime"] + GRACE_PERIOD_DURATION
    assert liquidation["lenderPeriodMaturity"] == liquidation["startTime"] + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION
    assert liquidation["principal"] == LOAN_AMOUNT
    assert liquidation["interestAmount"] == interest_amount
    assert liquidation["apr"] == apr
    assert liquidation["borrower"] == borrower
    assert liquidation["loanId"] == loan_id
    assert liquidation["loansCoreContract"] == loans_core_contract
    assert liquidation["erc20TokenContract"] == erc20_contract

    event = tx.events["LiquidationAdded"]
    assert event["liquidationId"] == liquidation_id
    assert event["collateralAddress"] == erc721_contract
    assert event["tokenId"] == 0
    assert event["erc20TokenContract"] == erc20_contract
    assert event["gracePeriodPrice"] == int(Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + Decimal(LOAN_AMOUNT * apr * GRACE_PERIOD_DURATION) / (Decimal(31536000) * Decimal(10000)))
    assert event["lenderPeriodPrice"] == int(Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + Decimal(LOAN_AMOUNT * apr * (GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION)) / (Decimal(31536000) * Decimal(10000)))
    assert event["gracePeriodMaturity"] == liquidation["startTime"] + GRACE_PERIOD_DURATION
    assert event["lenderPeriodMaturity"] == liquidation["startTime"] + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION
    assert event["loansCoreContract"] == loans_core_contract
    assert event["loanId"] == loan_id
    assert event["borrower"] == borrower


def test_add_liquidation_loan_not_defaulted(liquidations_peripheral_contract, liquidations_core_contract, loans_peripheral_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value

    with brownie.reverts("loan is not defaulted"):
        liquidations_peripheral_contract.addLiquidation(
            erc721_contract,
            0,
            borrower,
            loan_id,
            erc20_contract
        )


def test_add_liquidation_collat_not_in_loan(liquidations_peripheral_contract, liquidations_core_contract, loans_peripheral_contract, loans_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    erc721_contract.mint(collateral_vault_core_contract, 1, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    with brownie.reverts("collateral not in loan"):
        liquidations_peripheral_contract.addLiquidation(
            erc721_contract,
            1,
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
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    erc721_contract.mint(collateral_vault_core_contract, 1, {"from": contract_owner})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT / 2), (erc721_contract, 1, LOAN_AMOUNT / 2)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        1,
        borrower,
        loan_id,
        erc20_contract
    )

    liquidation_id1 = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)["lid"]
    liquidation_id2 = liquidations_peripheral_contract.getLiquidation(erc721_contract, 1)["lid"]

    interest_amount = int(Decimal(LOAN_AMOUNT) / Decimal(2) * Decimal(LOAN_INTEREST * (MATURITY - int(dt.now().timestamp()))) / Decimal(25920000000))
    apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

    grace_period_price = int(Decimal(LOAN_AMOUNT) / Decimal(2) + Decimal(interest_amount) + (Decimal(LOAN_AMOUNT) / Decimal(2) * Decimal(apr) * Decimal(GRACE_PERIOD_DURATION)) / (Decimal(31536000) * Decimal(10000)))
    erc20_contract.mint(borrower, grace_period_price * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, grace_period_price * 2, {"from": borrower})

    tx = liquidations_peripheral_contract.payLoanLiquidationsGracePeriod(loan_id, erc20_contract, {"from": borrower})

    # LIQUIDATION 1
    event_liquidation_removed1 = tx.events["LiquidationRemoved"][0]
    assert event_liquidation_removed1["liquidationId"] == liquidation_id1
    assert event_liquidation_removed1["collateralAddress"] == erc721_contract
    assert event_liquidation_removed1["tokenId"] == 0
    assert event_liquidation_removed1["erc20TokenContract"] == erc20_contract
    assert event_liquidation_removed1["loansCoreContract"] == loans_core_contract
    assert event_liquidation_removed1["loanId"] == loan_id
    assert event_liquidation_removed1["borrower"] == borrower

    event_nft_purchased1 = tx.events["NFTPurchased"][0]
    assert event_nft_purchased1["liquidationId"] == liquidation_id1
    assert event_nft_purchased1["collateralAddress"] == erc721_contract
    assert event_nft_purchased1["tokenId"] == 0
    assert event_nft_purchased1["amount"] == grace_period_price
    assert event_nft_purchased1["buyerAddress"] == borrower
    assert event_nft_purchased1["erc20TokenContract"] == erc20_contract
    assert event_nft_purchased1["method"] == "GRACE_PERIOD"

    # LIQUIDATION 2
    event_liquidation_removed2 = tx.events["LiquidationRemoved"][1]
    assert event_liquidation_removed2["liquidationId"] == liquidation_id2
    assert event_liquidation_removed2["collateralAddress"] == erc721_contract
    assert event_liquidation_removed2["tokenId"] == 1
    assert event_liquidation_removed2["erc20TokenContract"] == erc20_contract
    assert event_liquidation_removed2["loansCoreContract"] == loans_core_contract
    assert event_liquidation_removed2["loanId"] == loan_id
    assert event_liquidation_removed2["borrower"] == borrower

    event_nft_purchased2 = tx.events["NFTPurchased"][1]
    assert event_nft_purchased2["liquidationId"] == liquidation_id2
    assert event_nft_purchased2["collateralAddress"] == erc721_contract
    assert event_nft_purchased2["tokenId"] == 1
    assert event_nft_purchased2["amount"] == grace_period_price
    assert event_nft_purchased2["buyerAddress"] == borrower
    assert event_nft_purchased2["erc20TokenContract"] == erc20_contract
    assert event_nft_purchased2["method"] == "GRACE_PERIOD"

    for event in tx.events["FundsReceipt"]:
        assert event["fundsOrigin"] == "liquidation_grace_period"


def test_buy_nft_grace_period_collat_not_owned_by_vault(liquidations_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, contract_owner):
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(contract_owner, 0, {"from": contract_owner})

    with brownie.reverts("collateral not owned by vault"):
        liquidations_peripheral_contract.buyNFTGracePeriod(
            erc721_contract,
            0
        )


def test_buy_nft_grace_period_not_allowed(liquidations_peripheral_contract, liquidations_core_contract, loans_peripheral_contract, loans_core_contract, lending_pool_peripheral_contract, lending_pool_core_contract, collateral_vault_peripheral_contract, collateral_vault_core_contract, erc721_contract, erc20_contract, borrower, contract_owner):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})

    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    with brownie.reverts("msg.sender is not borrower"):
        liquidations_peripheral_contract.buyNFTGracePeriod(
            erc721_contract,
            0,
            {"from": contract_owner}
        )


def test_buy_nft_grace_period(
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
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    liquidation_id = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)["lid"]
    loan = loans_core_contract.getLoan(borrower, loan_id)

    interest_amount = int(Decimal(loan["amount"]) * Decimal(loan["interest"] * Decimal(loan["maturity"] - loan["startTime"])) / Decimal(25920000000))
    apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

    grace_period_price = int(Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + (Decimal(LOAN_AMOUNT) * Decimal(apr) * Decimal(GRACE_PERIOD_DURATION)) / (Decimal(31536000) * Decimal(10000)))
    erc20_contract.mint(borrower, grace_period_price, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, grace_period_price, {"from": borrower})

    tx = liquidations_peripheral_contract.buyNFTGracePeriod(
        erc721_contract,
        0,
        {"from": borrower}
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

    event_liquidation_removed = tx.events["LiquidationRemoved"]
    assert event_liquidation_removed["liquidationId"] == liquidation_id
    assert event_liquidation_removed["collateralAddress"] == erc721_contract
    assert event_liquidation_removed["tokenId"] == 0
    assert event_liquidation_removed["erc20TokenContract"] == erc20_contract
    assert event_liquidation_removed["loansCoreContract"] == loans_core_contract
    assert event_liquidation_removed["loanId"] == loan_id
    assert event_liquidation_removed["borrower"] == borrower

    event_nft_purchased = tx.events["NFTPurchased"]
    assert event_nft_purchased["liquidationId"] == liquidation_id
    assert event_nft_purchased["collateralAddress"] == erc721_contract
    assert event_nft_purchased["tokenId"] == 0
    assert event_nft_purchased["amount"] == grace_period_price
    assert event_nft_purchased["buyerAddress"] == borrower
    assert event_nft_purchased["erc20TokenContract"] == erc20_contract
    assert event_nft_purchased["method"] == "GRACE_PERIOD"

    event_funds_receipt = tx.events["FundsReceipt"]
    assert event_funds_receipt["fundsOrigin"] == "liquidation_grace_period"


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
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    with brownie.reverts("liquidation in grace period"):
        liquidations_peripheral_contract.buyNFTLenderPeriod(
            erc721_contract,
            0,
            {"from": borrower}
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
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION + 1)

    with brownie.reverts("liquidation out of lender period"):
        liquidations_peripheral_contract.buyNFTLenderPeriod(
            erc721_contract,
            0,
            {"from": borrower}
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
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})
    
    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION + 1)

    liquidation_id = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)["lid"]
    loan = loans_core_contract.getLoan(borrower, loan_id)

    interest_amount = int(Decimal(loan["amount"]) * Decimal(loan["interest"] * Decimal(loan["maturity"] - loan["startTime"])) / Decimal(25920000000))
    apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

    liquidation_price = int(Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + (Decimal(LOAN_AMOUNT) * Decimal(apr) * Decimal(GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION)) / (Decimal(31536000) * Decimal(10000)))
    erc20_contract.mint(borrower, liquidation_price, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, liquidation_price, {"from": borrower})

    print(liquidation_price)
    print(liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)["lenderPeriodPrice"])
    print(erc20_contract.balanceOf(borrower))
    print(erc20_contract.allowance(borrower, lending_pool_core_contract))

    tx = liquidations_peripheral_contract.buyNFTLenderPeriod(
        erc721_contract,
        0,
        {"from": borrower}
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

    event_liquidation_removed = tx.events["LiquidationRemoved"]
    assert event_liquidation_removed["liquidationId"] == liquidation_id
    assert event_liquidation_removed["collateralAddress"] == erc721_contract
    assert event_liquidation_removed["tokenId"] == 0
    assert event_liquidation_removed["erc20TokenContract"] == erc20_contract
    assert event_liquidation_removed["loansCoreContract"] == loans_core_contract
    assert event_liquidation_removed["loanId"] == loan_id
    assert event_liquidation_removed["borrower"] == borrower

    event_nft_purchased = tx.events["NFTPurchased"]
    assert event_nft_purchased["liquidationId"] == liquidation_id
    assert event_nft_purchased["collateralAddress"] == erc721_contract
    assert event_nft_purchased["tokenId"] == 0
    assert event_nft_purchased["amount"] == liquidation_price
    assert event_nft_purchased["buyerAddress"] == borrower
    assert event_nft_purchased["erc20TokenContract"] == erc20_contract
    assert event_nft_purchased["method"] == "LENDER_PERIOD"

    event_funds_receipt = tx.events["FundsReceipt"]
    assert event_funds_receipt["fundsOrigin"] == "liquidation_lenders_period"


def test_admin_withdrawal_wrong_sender(
    liquidations_peripheral_contract,
    erc721_contract,
    borrower,
    contract_owner
):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_peripheral_contract.adminWithdrawal(
            contract_owner,
            erc721_contract,
            0,
            {"from": borrower}
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
#     collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
#     collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    
#     liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

#     liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
#     liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
#     liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

#     loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

#     lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
#     lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
#     lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
#     lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

#     erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

#     erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
#     erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
#     lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
#     lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})
    
#     tx_add_loan = loans_core_contract.addLoan(
#         borrower,
#         LOAN_AMOUNT,
#         LOAN_INTEREST,
#         MATURITY,
#         [(erc721_contract, 0, LOAN_AMOUNT)],
#         {"from": loans_peripheral_contract}
#     )
#     loan_id = tx_add_loan.return_value
#     loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
#     loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

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
#         {"from": contract_owner}
#     )

#     liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
#     assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
#     assert liquidation["startTime"] == 0
#     assert liquidation["borrower"] == brownie.ZERO_ADDRESS
#     assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

#     event_liquidation_removed = tx.events["LiquidationRemoved"]
#     assert event_liquidation_removed["liquidationId"] == liquidation_id
#     assert event_liquidation_removed["collateralAddress"] == erc721_contract
#     assert event_liquidation_removed["tokenId"] == 0
#     assert event_liquidation_removed["erc20TokenContract"] == erc20_contract
#     assert event_liquidation_removed["loansCoreContract"] == loans_core_contract
#     assert event_liquidation_removed["loanId"] == loan_id
#     assert event_liquidation_removed["borrower"] == borrower

#     event_admin_withdrawal = tx.events["AdminWithdrawal"]
#     assert event_admin_withdrawal["liquidationId"] == liquidation_id
#     assert event_admin_withdrawal["collateralAddress"] == erc721_contract
#     assert event_admin_withdrawal["tokenId"] == 0
#     assert event_admin_withdrawal["wallet"] == contract_owner


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
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})

    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})

    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_core_contract, 0, {"from": contract_owner})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})
    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.deposit(LOAN_AMOUNT * 2, {"from": contract_owner})
    lending_pool_peripheral_contract.sendFunds(contract_owner, LOAN_AMOUNT, {"from": loans_peripheral_contract})

    erc20_contract.mint(contract_owner, LOAN_AMOUNT * 2, {"from": contract_owner})

    tx_add_loan = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract, 0, LOAN_AMOUNT)],
        {"from": loans_peripheral_contract}
    )
    loan_id = tx_add_loan.return_value
    loans_core_contract.updateLoanStarted(borrower, loan_id, {"from": loans_peripheral_contract})
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, {"from": loans_peripheral_contract})

    liquidations_peripheral_contract.addLiquidation(
        erc721_contract,
        0,
        borrower,
        loan_id,
        erc20_contract
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
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

    liquidation_id = liquidation['lid']
    collateral_address = liquidation['collateralAddress']
    token_id = liquidation['tokenId']
    loan_id = loan['id']

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION+LENDER_PERIOD_DURATION+1)
    liquidations_peripheral_contract.adminWithdrawal(contract_owner, collateral_address, token_id, {"from": contract_owner})

    erc20_contract.approve(lending_pool_core_contract, LOAN_AMOUNT, {"from": contract_owner})
    tx = liquidations_peripheral_contract.adminLiquidation(
        LOAN_AMOUNT*7//10,
        LOAN_AMOUNT*1//10,
        liquidation_id,
        liquidation['erc20TokenContract'],
        collateral_address,
        token_id,
        {"from": contract_owner}
    )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["lid"] == brownie.ZERO_ADDRESS
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

    assert "LiquidationRemoved" not in tx.events

    event_nft_purchased = tx.events["NFTPurchased"]
    assert event_nft_purchased["liquidationId"] == liquidation_id
    assert event_nft_purchased["collateralAddress"] == erc721_contract
    assert event_nft_purchased["tokenId"] == 0
    assert event_nft_purchased["amount"] == LOAN_AMOUNT * 8 // 10
    assert event_nft_purchased["buyerAddress"] == contract_owner
    assert event_nft_purchased["erc20TokenContract"] == erc20_contract
    assert event_nft_purchased["method"] == "BACKSTOP_PERIOD_ADMIN"

    event_funds_receipt = tx.events["FundsReceipt"]
    assert event_funds_receipt["fundsOrigin"] == "admin_liquidation"


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

    collateral_address = liquidation['collateralAddress']
    token_id = liquidation['tokenId']

    with brownie.reverts("msg.sender is not the owner"):
        tx = liquidations_peripheral_contract.adminLiquidation(
            LOAN_AMOUNT*7//10,
            LOAN_AMOUNT*1//10,
            liquidation['lid'],
            liquidation['erc20TokenContract'],
            collateral_address,
            token_id,
            {"from": borrower}
        )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["lid"] != brownie.ZERO_ADDRESS


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

    collateral_address = liquidation['collateralAddress']
    token_id = liquidation['tokenId']

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION+LENDER_PERIOD_DURATION-1)

    with brownie.reverts("collateral still owned by vault"):
        tx = liquidations_peripheral_contract.adminLiquidation(
            LOAN_AMOUNT*7//10,
            LOAN_AMOUNT*1//10,
            liquidation['lid'],
            liquidation['erc20TokenContract'],
            collateral_address,
            token_id,
            {"from": contract_owner}
        )

    liquidation = liquidations_peripheral_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["lid"] != brownie.ZERO_ADDRESS


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

    collateral_address = liquidation['collateralAddress']
    token_id = liquidation['tokenId']

    chain.mine(blocks=1, timedelta=GRACE_PERIOD_DURATION+LENDER_PERIOD_DURATION)
    collateral_vault_peripheral_contract.transferCollateralFromLiquidation(contract_owner, collateral_address, token_id, {"from": liquidations_peripheral_contract})

    with brownie.reverts("collateral still in liquidation"):
        tx = liquidations_peripheral_contract.adminLiquidation(
            LOAN_AMOUNT*7//10,
            LOAN_AMOUNT*1//10,
            liquidation['lid'],
            liquidation['erc20TokenContract'],
            collateral_address,
            token_id,
            {"from": contract_owner}
        )
