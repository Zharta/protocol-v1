from brownie.network import chain
from web3 import Web3

import brownie


GRACE_PERIOD_DURATION = 172800 # 2 days
BUY_NOW_PERIOD_DURATION = 604800 # 15 days
AUCTION_DURATION = 604800 # 15 days

PRINCIPAL = Web3.toWei(1, "ether")
INTEREST_AMOUNT = Web3.toWei(0.1, "ether")
APR = 200


def test_initial_state(buy_now_core_contract, contract_owner,):
    # Check if the constructor of the contract is set up properly
    assert buy_now_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(buy_now_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(buy_now_core_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        buy_now_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(buy_now_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        buy_now_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(buy_now_core_contract, contract_owner, borrower):
    tx = buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert buy_now_core_contract.owner() == contract_owner
    assert buy_now_core_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(buy_now_core_contract, contract_owner, borrower):
    buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(buy_now_core_contract, contract_owner, borrower):
    buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        buy_now_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(buy_now_core_contract, contract_owner, borrower):
    buy_now_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = buy_now_core_contract.claimOwnership({"from": borrower})

    assert buy_now_core_contract.owner() == borrower
    assert buy_now_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_buy_now_peripheral_address_wrong_sender(buy_now_core_contract, buy_now_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": borrower})


def test_set_buy_now_peripheral_address_zero_address(buy_now_core_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_core_contract.setBuyNowPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_buy_now_peripheral_address_not_contract(buy_now_core_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_core_contract.setBuyNowPeripheralAddress(contract_owner, {"from": contract_owner})


def test_set_buy_now_peripheral_address(buy_now_core_contract, buy_now_peripheral_contract, contract_owner):
    tx = buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    assert buy_now_core_contract.buyNowPeripheralAddress() == buy_now_peripheral_contract

    event = tx.events["BuyNowPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == buy_now_peripheral_contract


def test_set_buy_now_peripheral_address_same_address(buy_now_core_contract, buy_now_peripheral_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    assert buy_now_core_contract.buyNowPeripheralAddress() == buy_now_peripheral_contract

    with brownie.reverts("new value is the same"):
        buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})


def test_add_loans_core_address_wrong_sender(buy_now_core_contract, loans_core_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": borrower})


def test_add_loans_core_address_zero_address(buy_now_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_loans_core_address_not_contract(buy_now_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_loans_core_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    tx = buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    event = tx.events["LoansCoreAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_loans_core_address_same_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    with brownie.reverts("new value is the same"):
        buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})


def test_remove_loans_core_address_wrong_sender(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        buy_now_core_contract.removeLoansCoreAddress(erc20_contract, {"from": borrower})


def test_remove_loans_core_address_zero_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        buy_now_core_contract.removeLoansCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_loans_core_address_not_contract(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        buy_now_core_contract.removeLoansCoreAddress(contract_owner, {"from": contract_owner})


def test_remove_loans_core_address_not_found(buy_now_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        buy_now_core_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})


def test_remove_loans_core_address(buy_now_core_contract, loans_core_contract, erc20_contract, contract_owner):
    buy_now_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    tx = buy_now_core_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})

    assert buy_now_core_contract.loansCoreAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LoansCoreAddressRemoved"]
    assert event["currentValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_liquidation_wrong_sender(buy_now_core_contract, borrower):
    with brownie.reverts("msg.sender is not BNPeriph addr"):
        buy_now_core_contract.addLiquidation(
            brownie.ZERO_ADDRESS,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            brownie.ZERO_ADDRESS,
            brownie.ZERO_ADDRESS,
            {"from": borrower}
        )


def test_add_liquidation(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_peripheral_contract, 0, {"from": contract_owner})

    grace_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) / 365
    buy_now_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) / 365

    start_time = chain.time()
    tx = buy_now_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        grace_period_price,
        buy_now_period_price,
        borrower,
        erc20_contract,
        {"from": buy_now_peripheral_contract}
    )

    liquidation = buy_now_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["startTime"] == start_time
    assert liquidation["gracePeriodMaturity"] == start_time + GRACE_PERIOD_DURATION
    assert liquidation["buyNowPeriodMaturity"] == start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION
    assert liquidation["principal"] == PRINCIPAL
    assert liquidation["interestAmount"] == INTEREST_AMOUNT
    assert liquidation["apr"] == APR
    assert liquidation["gracePeriodPrice"] == grace_period_price
    assert liquidation["buyNowPeriodPrice"] == buy_now_period_price
    assert liquidation["borrower"] == borrower
    assert liquidation["erc20TokenContract"] == erc20_contract


def test_add_liquidation_already_exists(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_peripheral_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    buy_now_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) / 365,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) / 365,
        borrower,
        erc20_contract,
        {"from": buy_now_peripheral_contract}
    )

    with brownie.reverts("liquidation already exists"):
        buy_now_core_contract.addLiquidation(
            erc721_contract,
            0,
            start_time,
            start_time + GRACE_PERIOD_DURATION,
            start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) / 365,
            PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) / 365,
            borrower,
            erc20_contract,
            {"from": buy_now_peripheral_contract}
        )


def test_remove_liquidation_wrong_sender(buy_now_core_contract, erc721_contract, contract_owner):
    with brownie.reverts("msg.sender is not BNPeriph addr"):
        buy_now_core_contract.removeLiquidation(erc721_contract, 0, {"from": contract_owner})


def test_remove_liquidation_not_found(buy_now_core_contract, buy_now_peripheral_contract, erc721_contract, contract_owner):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("liquidation not found"):
        buy_now_core_contract.removeLiquidation(erc721_contract, 0, {"from": buy_now_peripheral_contract})


def test_remove_liquidation(buy_now_core_contract, buy_now_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    buy_now_core_contract.setBuyNowPeripheralAddress(buy_now_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_peripheral_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    buy_now_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) / 365,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) / 365,
        borrower,
        erc20_contract,
        {"from": buy_now_peripheral_contract}
    )
    
    tx = buy_now_core_contract.removeLiquidation(erc721_contract, 0, {"from": buy_now_peripheral_contract})

    liquidation = buy_now_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

