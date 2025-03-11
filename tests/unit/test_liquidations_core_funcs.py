import boa
import eth_abi
import pytest
from web3 import Web3

from ..conftest_base import ZERO_ADDRESS

GRACE_PERIOD_DURATION = 172800  # 2 days
LENDER_PERIOD_DURATION = 604800  # 15 days
AUCTION_DURATION = 604800  # 15 days

PRINCIPAL = Web3.to_wei(1, "ether")
INTEREST_AMOUNT = Web3.to_wei(0.1, "ether")
APR = 200


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def investor():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def liquidations_core(liquidations_core_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return liquidations_core_contract.deploy()


def test_add_liquidation_wrong_sender(liquidations_core, borrower):
    with boa.reverts("msg.sender is not LiqPeriph addr"):
        liquidations_core.addLiquidation(
            ZERO_ADDRESS, 0, 0, 0, 0, 0, 0, 0, 0, 0, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, sender=borrower
        )


def test_add_liquidation(liquidations_core, contract_owner, borrower):
    loans_core = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    erc20 = boa.env.generate_address()
    liquidations_peripheral = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    grace_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 2) // 365
    liquidations_period_price = PRINCIPAL + INTEREST_AMOUNT + (PRINCIPAL * APR * 17) // 365

    start_time = boa.eval("block.timestamp")
    liquidations_core.addLiquidation(
        erc721,
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
        loans_core,
        erc20,
        sender=liquidations_peripheral,
    )

    liquidation_id_abi_encoded = eth_abi.encode(["address", "uint256", "uint256"], [erc721, 0, start_time])
    liquidation_id = Web3.solidity_keccak(["bytes32"], [liquidation_id_abi_encoded]).hex()

    liquidation = liquidations_core.getLiquidation(erc721, 0)
    assert liquidation[0].hex() == liquidation_id
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
    assert liquidation[13] == loans_core
    assert liquidation[14] == erc20


def test_add_liquidation_already_exists(liquidations_core, contract_owner, borrower):
    loans_core = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    erc20 = boa.env.generate_address()
    liquidations_peripheral = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    start_time = boa.eval("block.timestamp")
    liquidations_core.addLiquidation(
        erc721,
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
        loans_core,
        erc20,
        sender=liquidations_peripheral,
    )

    with boa.reverts("liquidation already exists"):
        liquidations_core.addLiquidation(
            erc721,
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
            loans_core,
            erc20,
            sender=liquidations_peripheral,
        )


def test_add_loan_to_liquidated_wrong_sender(liquidations_core, contract_owner):
    loans_core = boa.env.generate_address()
    with boa.reverts("msg.sender is not LiqPeriph addr"):
        liquidations_core.addLoanToLiquidated(contract_owner, loans_core, 0)


def test_add_loan_to_liquidated(liquidations_core, contract_owner, borrower):
    loans_core = boa.env.generate_address()
    liquidations_peripheral = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    liquidations_core.addLoanToLiquidated(borrower, loans_core, 0, sender=liquidations_peripheral)

    assert liquidations_core.isLoanLiquidated(borrower, loans_core, 0)


def test_remove_liquidation_wrong_sender(liquidations_core, contract_owner):
    erc721 = boa.env.generate_address()
    with boa.reverts("msg.sender is not LiqPeriph addr"):
        liquidations_core.removeLiquidation(erc721, 0)


def test_remove_liquidation_not_found(liquidations_core, contract_owner):
    liquidations_peripheral = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    with boa.reverts("liquidation not found"):
        liquidations_core.removeLiquidation(erc721, 0, sender=liquidations_peripheral)


def test_remove_liquidation(liquidations_core, contract_owner, borrower):
    loans_core = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    erc20 = boa.env.generate_address()
    liquidations_peripheral = boa.env.generate_address()
    liquidations_core.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)

    start_time = boa.eval("block.timestamp")
    liquidations_core.addLiquidation(
        erc721,
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
        loans_core,
        erc20,
        sender=liquidations_peripheral,
    )

    liquidations_core.removeLiquidation(erc721, 0, sender=liquidations_peripheral)

    liquidation = liquidations_core.getLiquidation(erc721, 0)
    assert liquidation[1] == ZERO_ADDRESS
    assert liquidation[3] == 0
    assert liquidation[11] == ZERO_ADDRESS
    assert liquidation[14] == ZERO_ADDRESS
