from brownie.network import chain
from web3 import Web3

import brownie
import eth_abi


GRACE_PERIOD_DURATION = 172800 # 2 days
BUY_NOW_PERIOD_DURATION = 604800 # 15 days
AUCTION_DURATION = 604800 # 15 days

PRINCIPAL = Web3.toWei(1, "ether")
INTEREST_AMOUNT = Web3.toWei(0.1, "ether")
APR = 200


def test_initial_state(liquidations_core_contract, contract_owner,):
    # Check if the constructor of the contract is set up properly
    assert liquidations_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(liquidations_core_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_core_contract.proposeOwner(borrower, {"from": borrower})


def test_propose_owner_zero_address(liquidations_core_contract, contract_owner):
    with brownie.reverts("address it the zero address"):
        liquidations_core_contract.proposeOwner(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_propose_owner_same_owner(liquidations_core_contract, contract_owner):
    with brownie.reverts("proposed owner addr is the owner"):
        liquidations_core_contract.proposeOwner(contract_owner, {"from": contract_owner})


def test_propose_owner(liquidations_core_contract, contract_owner, borrower):
    tx = liquidations_core_contract.proposeOwner(borrower, {"from": contract_owner})

    assert liquidations_core_contract.owner() == contract_owner
    assert liquidations_core_contract.proposedOwner() == borrower

    event = tx.events["OwnerProposed"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_propose_owner_same_proposed(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower, {"from": contract_owner})
    
    with brownie.reverts("proposed owner addr is the same"):
        liquidations_core_contract.proposeOwner(borrower, {"from": contract_owner})


def test_claim_ownership_wrong_sender(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower, {"from": contract_owner})

    with brownie.reverts("msg.sender is not the proposed"):
        liquidations_core_contract.claimOwnership({"from": contract_owner})


def test_claim_ownership(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower, {"from": contract_owner})

    tx = liquidations_core_contract.claimOwnership({"from": borrower})

    assert liquidations_core_contract.owner() == borrower
    assert liquidations_core_contract.proposedOwner() == brownie.ZERO_ADDRESS

    event = tx.events["OwnershipTransferred"]
    assert event["owner"] == contract_owner
    assert event["proposedOwner"] == borrower


def test_set_liquidations_peripheral_address_wrong_sender(liquidations_core_contract, liquidations_peripheral_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": borrower})


def test_set_liquidations_peripheral_address_zero_address(liquidations_core_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_set_liquidations_peripheral_address_not_contract(liquidations_core_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(contract_owner, {"from": contract_owner})


def test_set_liquidations_peripheral_address(liquidations_core_contract, liquidations_peripheral_contract, contract_owner):
    tx = liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    assert liquidations_core_contract.liquidationsPeripheralAddress() == liquidations_peripheral_contract

    event = tx.events["LiquidationsPeripheralAddressSet"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == liquidations_peripheral_contract


def test_set_liquidations_peripheral_address_same_address(liquidations_core_contract, liquidations_peripheral_contract, contract_owner):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    assert liquidations_core_contract.liquidationsPeripheralAddress() == liquidations_peripheral_contract

    with brownie.reverts("new value is the same"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})


def test_add_loans_core_address_wrong_sender(liquidations_core_contract, loans_core_contract, erc20_contract, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": borrower})


def test_add_loans_core_address_zero_address(liquidations_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is the zero addr"):
        liquidations_core_contract.addLoansCoreAddress(erc20_contract, brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_add_loans_core_address_not_contract(liquidations_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address is not a contract"):
        liquidations_core_contract.addLoansCoreAddress(erc20_contract, contract_owner, {"from": contract_owner})


def test_add_loans_core_address(liquidations_core_contract, loans_core_contract, erc20_contract, contract_owner):
    tx = liquidations_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert liquidations_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    event = tx.events["LoansCoreAddressAdded"]
    assert event["currentValue"] == brownie.ZERO_ADDRESS
    assert event["newValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_loans_core_address_same_address(liquidations_core_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert liquidations_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    with brownie.reverts("new value is the same"):
        liquidations_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})


def test_remove_loans_core_address_wrong_sender(liquidations_core_contract, loans_core_contract, erc20_contract, contract_owner, borrower):
    with brownie.reverts("msg.sender is not the owner"):
        liquidations_core_contract.removeLoansCoreAddress(erc20_contract, {"from": borrower})


def test_remove_loans_core_address_zero_address(liquidations_core_contract, loans_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is the zero addr"):
        liquidations_core_contract.removeLoansCoreAddress(brownie.ZERO_ADDRESS, {"from": contract_owner})


def test_remove_loans_core_address_not_contract(liquidations_core_contract, loans_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("erc20TokenAddr is not a contract"):
        liquidations_core_contract.removeLoansCoreAddress(contract_owner, {"from": contract_owner})


def test_remove_loans_core_address_not_found(liquidations_core_contract, erc20_contract, contract_owner):
    with brownie.reverts("address not found"):
        liquidations_core_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})


def test_remove_loans_core_address(liquidations_core_contract, loans_core_contract, erc20_contract, contract_owner):
    liquidations_core_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})

    assert liquidations_core_contract.loansCoreAddresses(erc20_contract) == loans_core_contract

    tx = liquidations_core_contract.removeLoansCoreAddress(erc20_contract, {"from": contract_owner})

    assert liquidations_core_contract.loansCoreAddresses(erc20_contract) == brownie.ZERO_ADDRESS

    event = tx.events["LoansCoreAddressRemoved"]
    assert event["currentValue"] == loans_core_contract
    assert event["erc20TokenContract"] == erc20_contract


def test_add_liquidation_wrong_sender(liquidations_core_contract, borrower):
    with brownie.reverts("msg.sender is not BNPeriph addr"):
        liquidations_core_contract.addLiquidation(
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


def test_add_liquidation(liquidations_core_contract, liquidations_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_peripheral_contract, 0, {"from": contract_owner})

    grace_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) / 365
    liquidations_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) / 365

    start_time = chain.time()
    tx = liquidations_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        grace_period_price,
        liquidations_period_price,
        borrower,
        erc20_contract,
        {"from": liquidations_peripheral_contract}
    )

    liquidation_id_abi_encoded = eth_abi.encode_abi(
        ["address", "uint256", "uint256"],
        [erc721_contract.address, 0, start_time]
    ).hex()
    liquidation_id = Web3.solidityKeccak(
        ["bytes32"],
        ["0x" + liquidation_id_abi_encoded]
    ).hex()

    liquidation = liquidations_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["lid"] == liquidation_id
    assert liquidation["startTime"] == start_time
    assert liquidation["gracePeriodMaturity"] == start_time + GRACE_PERIOD_DURATION
    assert liquidation["buyNowPeriodMaturity"] == start_time + GRACE_PERIOD_DURATION + BUY_NOW_PERIOD_DURATION
    assert liquidation["principal"] == PRINCIPAL
    assert liquidation["interestAmount"] == INTEREST_AMOUNT
    assert liquidation["apr"] == APR
    assert liquidation["gracePeriodPrice"] == grace_period_price
    assert liquidation["buyNowPeriodPrice"] == liquidations_period_price
    assert liquidation["borrower"] == borrower
    assert liquidation["erc20TokenContract"] == erc20_contract


def test_add_liquidation_already_exists(liquidations_core_contract, liquidations_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_peripheral_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    liquidations_core_contract.addLiquidation(
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
        {"from": liquidations_peripheral_contract}
    )

    with brownie.reverts("liquidation already exists"):
        liquidations_core_contract.addLiquidation(
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
            {"from": liquidations_peripheral_contract}
        )


def test_remove_liquidation_wrong_sender(liquidations_core_contract, erc721_contract, contract_owner):
    with brownie.reverts("msg.sender is not BNPeriph addr"):
        liquidations_core_contract.removeLiquidation(erc721_contract, 0, {"from": contract_owner})


def test_remove_liquidation_not_found(liquidations_core_contract, liquidations_peripheral_contract, erc721_contract, contract_owner):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    with brownie.reverts("liquidation not found"):
        liquidations_core_contract.removeLiquidation(erc721_contract, 0, {"from": liquidations_peripheral_contract})


def test_remove_liquidation(liquidations_core_contract, liquidations_peripheral_contract, collateral_vault_peripheral_contract, erc721_contract, erc20_contract, contract_owner, borrower):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})

    erc721_contract.mint(collateral_vault_peripheral_contract, 0, {"from": contract_owner})

    start_time = chain.time()
    liquidations_core_contract.addLiquidation(
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
        {"from": liquidations_peripheral_contract}
    )
    
    tx = liquidations_core_contract.removeLiquidation(erc721_contract, 0, {"from": liquidations_peripheral_contract})

    liquidation = liquidations_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation["collateralAddress"] == brownie.ZERO_ADDRESS
    assert liquidation["startTime"] == 0
    assert liquidation["borrower"] == brownie.ZERO_ADDRESS
    assert liquidation["erc20TokenContract"] == brownie.ZERO_ADDRESS

