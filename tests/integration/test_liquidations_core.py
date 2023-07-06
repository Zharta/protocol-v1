from web3 import Web3

import boa
import eth_abi

from ..conftest_base import ZERO_ADDRESS, get_last_event

GRACE_PERIOD_DURATION = 172800  # 2 days
LENDER_PERIOD_DURATION = 604800  # 15 days
AUCTION_DURATION = 604800  # 15 days

PRINCIPAL = Web3.to_wei(1, "ether")
INTEREST_AMOUNT = Web3.to_wei(0.1, "ether")
APR = 200


def test_initial_state(liquidations_core_contract, contract_owner,):
    # Check if the constructor of the contract is set up properly
    assert liquidations_core_contract.owner() == contract_owner


def test_propose_owner_wrong_sender(liquidations_core_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_core_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(liquidations_core_contract, contract_owner):
    with boa.reverts("address it the zero address"):
        liquidations_core_contract.proposeOwner(ZERO_ADDRESS)


def test_propose_owner_same_owner(liquidations_core_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        liquidations_core_contract.proposeOwner(contract_owner)


def test_propose_owner(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower)
    event = get_last_event(liquidations_core_contract, name="OwnerProposed")

    assert liquidations_core_contract.owner() == contract_owner
    assert liquidations_core_contract.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower)

    with boa.reverts("proposed owner addr is the same"):
        liquidations_core_contract.proposeOwner(borrower)


def test_claim_ownership_wrong_sender(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower)

    with boa.reverts("msg.sender is not the proposed"):
        liquidations_core_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(liquidations_core_contract, contract_owner, borrower):
    liquidations_core_contract.proposeOwner(borrower)

    liquidations_core_contract.claimOwnership(sender=borrower)
    event = get_last_event(liquidations_core_contract, name="OwnershipTransferred")

    assert liquidations_core_contract.owner() == borrower
    assert liquidations_core_contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_liquidations_peripheral_address_wrong_sender(liquidations_core_contract, liquidations_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, sender=borrower)


def test_set_liquidations_peripheral_address_zero_address(liquidations_core_contract, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(ZERO_ADDRESS)


def test_set_liquidations_peripheral_address_not_contract(liquidations_core_contract, contract_owner):
    with boa.reverts("address is not a contract"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(contract_owner)


def test_set_liquidations_peripheral_address(liquidations_core_contract, liquidations_peripheral_contract, contract_owner):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)
    event = get_last_event(liquidations_core_contract, name="LiquidationsPeripheralAddressSet")

    assert liquidations_core_contract.liquidationsPeripheralAddress() == liquidations_peripheral_contract.address

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == liquidations_peripheral_contract.address


def test_set_liquidations_peripheral_address_same_address(liquidations_core_contract, liquidations_peripheral_contract, contract_owner):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

    assert liquidations_core_contract.liquidationsPeripheralAddress() == liquidations_peripheral_contract.address

    with boa.reverts("new value is the same"):
        liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)


def test_add_liquidation_wrong_sender(liquidations_core_contract, borrower):
    with boa.reverts("msg.sender is not LiqPeriph addr"):
        liquidations_core_contract.addLiquidation(
            ZERO_ADDRESS,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            sender=borrower
        )


def test_add_liquidation(
    liquidations_core_contract,
    liquidations_peripheral_contract,
    collateral_vault_peripheral_contract,
    loans_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower
):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

    erc721_contract.mint(collateral_vault_peripheral_contract, 0)

    grace_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) // 365
    liquidations_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) // 365

    start_time = boa.eval("block.timestamp")
    liquidations_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        grace_period_price,
        liquidations_period_price,
        borrower,
        0,
        loans_core_contract,
        erc20_contract,
        sender=liquidations_peripheral_contract.address
    )

    liquidation_id_abi_encoded = eth_abi.encode(
        ["address", "uint256", "uint256"],
        [erc721_contract.address, 0, start_time]
    )
    liquidation_id = Web3.solidity_keccak(["bytes32"], [liquidation_id_abi_encoded]).hex()

    liquidation = liquidations_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation[0].hex() == liquidation_id[2:]
    assert liquidation[3] == start_time
    assert liquidation[4] == start_time + GRACE_PERIOD_DURATION
    assert liquidation[5] == start_time + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION
    assert liquidation[6] == PRINCIPAL
    assert liquidation[7] == INTEREST_AMOUNT
    assert liquidation[8] == APR
    assert liquidation[9] == grace_period_price
    assert liquidation[10] == liquidations_period_price
    assert liquidation[11] == borrower
    assert liquidation[12] == 0
    assert liquidation[13] == loans_core_contract.address
    assert liquidation[14] == erc20_contract.address


def test_add_liquidation_already_exists(
    liquidations_core_contract,
    liquidations_peripheral_contract,
    collateral_vault_peripheral_contract,
    loans_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower
):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

    erc721_contract.mint(collateral_vault_peripheral_contract, 0)

    start_time = boa.eval("block.timestamp")
    liquidations_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) // 365,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) // 365,
        borrower,
        0,
        loans_core_contract,
        erc20_contract,
        sender=liquidations_peripheral_contract.address
    )

    with boa.reverts("liquidation already exists"):
        liquidations_core_contract.addLiquidation(
            erc721_contract,
            0,
            start_time,
            start_time + GRACE_PERIOD_DURATION,
            start_time + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION,
            PRINCIPAL,
            INTEREST_AMOUNT,
            APR,
            PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) // 365,
            PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) // 365,
            borrower,
            0,
            loans_core_contract,
            erc20_contract,
            sender=liquidations_peripheral_contract.address
        )


def test_add_loan_to_liquidated_wrong_sender(liquidations_core_contract, loans_core_contract, contract_owner):
    with boa.reverts("msg.sender is not LiqPeriph addr"):
        liquidations_core_contract.addLoanToLiquidated(contract_owner, loans_core_contract, 0)


def test_add_loan_to_liquidated(
    liquidations_core_contract,
    liquidations_peripheral_contract,
    loans_core_contract,
    contract_owner,
    borrower
):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

    liquidations_core_contract.addLoanToLiquidated(
        borrower,
        loans_core_contract,
        0,
        sender=liquidations_peripheral_contract.address
    )

    assert liquidations_core_contract.isLoanLiquidated(borrower, loans_core_contract, 0)


def test_remove_liquidation_wrong_sender(liquidations_core_contract, erc721_contract, contract_owner):
    with boa.reverts("msg.sender is not LiqPeriph addr"):
        liquidations_core_contract.removeLiquidation(erc721_contract, 0)


def test_remove_liquidation_not_found(liquidations_core_contract, liquidations_peripheral_contract, erc721_contract, contract_owner):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

    with boa.reverts("liquidation not found"):
        liquidations_core_contract.removeLiquidation(erc721_contract, 0, sender=liquidations_peripheral_contract.address)


def test_remove_liquidation(
    liquidations_core_contract,
    liquidations_peripheral_contract,
    collateral_vault_peripheral_contract,
    loans_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower
):
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract)

    erc721_contract.mint(collateral_vault_peripheral_contract, 0)

    start_time = boa.eval("block.timestamp")
    liquidations_core_contract.addLiquidation(
        erc721_contract,
        0,
        start_time,
        start_time + GRACE_PERIOD_DURATION,
        start_time + GRACE_PERIOD_DURATION + LENDER_PERIOD_DURATION,
        PRINCIPAL,
        INTEREST_AMOUNT,
        APR,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) // 365,
        PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) // 365,
        borrower,
        0,
        loans_core_contract,
        erc20_contract,
        sender=liquidations_peripheral_contract.address
    )

    liquidations_core_contract.removeLiquidation(erc721_contract, 0, sender=liquidations_peripheral_contract.address)

    # liquidation = checksummed(liquidations_core_contract.getLiquidation(erc721_contract, 0))
    liquidation = liquidations_core_contract.getLiquidation(erc721_contract, 0)
    assert liquidation[1] == ZERO_ADDRESS
    assert liquidation[3] == 0
    assert liquidation[11] == ZERO_ADDRESS
    assert liquidation[14] == ZERO_ADDRESS

