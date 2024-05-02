import boa
import pytest
from web3 import Web3

from ..conftest_base import ZERO_ADDRESS, get_last_event

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
def erc20():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def liquidations_core(liquidations_core_contract, erc20, contract_owner):
    with boa.env.prank(contract_owner):
        return liquidations_core_contract.deploy()


@pytest.fixture(scope="module")
def liquidations_peripheral(liquidations_peripheral_contract, liquidations_core, erc20, contract_owner):
    with boa.env.prank(contract_owner):
        return liquidations_peripheral_contract.deploy(
            liquidations_core, GRACE_PERIOD_DURATION, LENDER_PERIOD_DURATION, AUCTION_DURATION, erc20
        )


def test_add_loans_core_address(liquidations_peripheral, erc20, contract_owner):
    loans_core = boa.env.generate_address()
    liquidations_peripheral.addLoansCoreAddress(erc20, loans_core, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="LoansCoreAddressAdded")

    assert liquidations_peripheral.loansCoreAddresses(erc20) == loans_core

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_core
    assert event.erc20TokenContract == erc20


def test_add_loans_core_address_same_address(liquidations_peripheral, erc20, contract_owner):
    loans_core = boa.env.generate_address()
    liquidations_peripheral.addLoansCoreAddress(erc20, loans_core, sender=contract_owner)

    assert liquidations_peripheral.loansCoreAddresses(erc20) == loans_core

    with boa.reverts("new value is the same"):
        liquidations_peripheral.addLoansCoreAddress(erc20, loans_core, sender=contract_owner)


def test_remove_loans_core_address_not_found(liquidations_peripheral, erc20, contract_owner):
    with boa.reverts("address not found"):
        liquidations_peripheral.removeLoansCoreAddress(erc20, sender=contract_owner)


def test_remove_loans_core_address(liquidations_peripheral, erc20, contract_owner):
    loans_core = boa.env.generate_address()
    liquidations_peripheral.addLoansCoreAddress(erc20, loans_core, sender=contract_owner)

    assert liquidations_peripheral.loansCoreAddresses(erc20) == loans_core

    liquidations_peripheral.removeLoansCoreAddress(erc20, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="LoansCoreAddressRemoved")

    assert liquidations_peripheral.loansCoreAddresses(erc20) == ZERO_ADDRESS

    assert event.currentValue == loans_core
    assert event.erc20TokenContract == erc20


def test_add_lending_pool_peripheral_address(liquidations_peripheral, erc20, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    liquidations_peripheral.addLendingPoolPeripheralAddress(erc20, lending_pool_peripheral, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="LendingPoolPeripheralAddressAdded")

    assert liquidations_peripheral.lendingPoolPeripheralAddresses(erc20) == lending_pool_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == lending_pool_peripheral
    assert event.erc20TokenContract == erc20


def test_add_lending_pool_peripheral_address_same_address(liquidations_peripheral, erc20, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    liquidations_peripheral.addLendingPoolPeripheralAddress(erc20, lending_pool_peripheral, sender=contract_owner)

    assert liquidations_peripheral.lendingPoolPeripheralAddresses(erc20) == lending_pool_peripheral

    with boa.reverts("new value is the same"):
        liquidations_peripheral.addLendingPoolPeripheralAddress(erc20, lending_pool_peripheral, sender=contract_owner)


def test_remove_lending_pool_peripheral_address_not_found(liquidations_peripheral, erc20, contract_owner):
    with boa.reverts("address not found"):
        liquidations_peripheral.removeLendingPoolPeripheralAddress(erc20, sender=contract_owner)


def test_remove_lending_pool_peripheral_address(liquidations_peripheral, erc20, contract_owner):
    lending_pool_peripheral = boa.env.generate_address()
    liquidations_peripheral.addLendingPoolPeripheralAddress(erc20, lending_pool_peripheral, sender=contract_owner)

    assert liquidations_peripheral.lendingPoolPeripheralAddresses(erc20) == lending_pool_peripheral

    liquidations_peripheral.removeLendingPoolPeripheralAddress(erc20, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="LendingPoolPeripheralAddressRemoved")

    assert liquidations_peripheral.lendingPoolPeripheralAddresses(erc20) == ZERO_ADDRESS

    assert event.currentValue == lending_pool_peripheral
    assert event.erc20TokenContract == erc20


def test_set_collateral_vault_address(liquidations_peripheral, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="CollateralVaultPeripheralAddressSet")

    assert liquidations_peripheral.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral


def test_set_collateral_vault_address_same_address(liquidations_peripheral, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    assert liquidations_peripheral.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    with boa.reverts("new value is the same"):
        liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)


def test_set_collateral_vault_address(liquidations_peripheral, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="CollateralVaultPeripheralAddressSet")

    assert liquidations_peripheral.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == collateral_vault_peripheral


def test_set_collateral_vault_address_same_address(liquidations_peripheral, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    assert liquidations_peripheral.collateralVaultPeripheralAddress() == collateral_vault_peripheral

    with boa.reverts("new value is the same"):
        liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)


def test_initial_state(liquidations_peripheral, liquidations_core, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert liquidations_peripheral.owner() == contract_owner
    assert liquidations_peripheral.liquidationsCoreAddress() == liquidations_core.address
    assert liquidations_peripheral.gracePeriodDuration() == GRACE_PERIOD_DURATION
    assert liquidations_peripheral.lenderPeriodDuration() == LENDER_PERIOD_DURATION
    assert liquidations_peripheral.auctionPeriodDuration() == AUCTION_DURATION


def test_propose_owner_wrong_sender(liquidations_peripheral, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(liquidations_peripheral, contract_owner):
    with boa.reverts("address it the zero address"):
        liquidations_peripheral.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(liquidations_peripheral, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        liquidations_peripheral.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(liquidations_peripheral, contract_owner, borrower):
    liquidations_peripheral.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="OwnerProposed")

    assert liquidations_peripheral.owner() == contract_owner
    assert liquidations_peripheral.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(liquidations_peripheral, contract_owner, borrower):
    liquidations_peripheral.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        liquidations_peripheral.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(liquidations_peripheral, contract_owner, borrower):
    liquidations_peripheral.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        liquidations_peripheral.claimOwnership(sender=contract_owner)


def test_claim_ownership(liquidations_peripheral, contract_owner, borrower):
    liquidations_peripheral.proposeOwner(borrower, sender=contract_owner)

    liquidations_peripheral.claimOwnership(sender=borrower)
    event = get_last_event(liquidations_peripheral, name="OwnershipTransferred")

    assert liquidations_peripheral.owner() == borrower
    assert liquidations_peripheral.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_grace_period_duration_wrong_sender(liquidations_peripheral, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.setGracePeriodDuration(0, sender=borrower)


def test_set_grace_period_duration_zero_value(liquidations_peripheral, contract_owner):
    with boa.reverts("duration is 0"):
        liquidations_peripheral.setGracePeriodDuration(0, sender=contract_owner)


def test_set_grace_period_duration(liquidations_peripheral, contract_owner):
    assert liquidations_peripheral.gracePeriodDuration() == GRACE_PERIOD_DURATION

    liquidations_peripheral.setGracePeriodDuration(GRACE_PERIOD_DURATION + 1, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="GracePeriodDurationChanged")

    assert liquidations_peripheral.gracePeriodDuration() == GRACE_PERIOD_DURATION + 1

    assert event.currentValue == GRACE_PERIOD_DURATION
    assert event.newValue == GRACE_PERIOD_DURATION + 1


def test_set_grace_period_duration_same_value(liquidations_peripheral, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral.setGracePeriodDuration(GRACE_PERIOD_DURATION, sender=contract_owner)


def test_set_lenders_period_duration_wrong_sender(liquidations_peripheral, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.setLendersPeriodDuration(0, sender=borrower)


def test_set_lenders_period_duration_zero_value(liquidations_peripheral, contract_owner):
    with boa.reverts("duration is 0"):
        liquidations_peripheral.setLendersPeriodDuration(0, sender=contract_owner)


def test_set_lenders_period_duration(liquidations_peripheral, contract_owner):
    assert liquidations_peripheral.lenderPeriodDuration() == LENDER_PERIOD_DURATION

    liquidations_peripheral.setLendersPeriodDuration(LENDER_PERIOD_DURATION + 1, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="LendersPeriodDurationChanged")

    assert liquidations_peripheral.lenderPeriodDuration() == LENDER_PERIOD_DURATION + 1

    assert event.currentValue == LENDER_PERIOD_DURATION
    assert event.newValue == LENDER_PERIOD_DURATION + 1


def test_set_lenders_period_duration_same_value(liquidations_peripheral, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral.setLendersPeriodDuration(LENDER_PERIOD_DURATION, sender=contract_owner)


def test_set_auction_period_duration_wrong_sender(liquidations_peripheral, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.setAuctionPeriodDuration(0, sender=borrower)


def test_set_auction_period_duration_zero_value(liquidations_peripheral, contract_owner):
    with boa.reverts("duration is 0"):
        liquidations_peripheral.setAuctionPeriodDuration(0, sender=contract_owner)


def test_set_auction_period_duration(liquidations_peripheral, contract_owner):
    assert liquidations_peripheral.auctionPeriodDuration() == AUCTION_DURATION

    liquidations_peripheral.setAuctionPeriodDuration(AUCTION_DURATION + 1, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="AuctionPeriodDurationChanged")

    assert liquidations_peripheral.auctionPeriodDuration() == AUCTION_DURATION + 1

    assert event.currentValue == AUCTION_DURATION
    assert event.newValue == AUCTION_DURATION + 1


def test_set_auction_period_duration_same_value(liquidations_peripheral, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral.setAuctionPeriodDuration(AUCTION_DURATION, sender=contract_owner)


def test_set_liquidations_core_address_wrong_sender(liquidations_peripheral, liquidations_core, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.setLiquidationsCoreAddress(liquidations_core, sender=borrower)


def test_set_liquidations_core_address_zero_address(liquidations_peripheral, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral.setLiquidationsCoreAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_liquidations_core_address(liquidations_peripheral, liquidations_core, contract_owner):
    loans_core = boa.env.generate_address()
    liquidations_peripheral.setLiquidationsCoreAddress(loans_core, sender=contract_owner)
    event = get_last_event(liquidations_peripheral, name="LiquidationsCoreAddressSet")

    assert liquidations_peripheral.liquidationsCoreAddress() == loans_core

    assert event.currentValue == liquidations_core.address
    assert event.newValue == loans_core


def test_set_liquidations_core_address_same_address(liquidations_peripheral, liquidations_core, contract_owner):
    with boa.reverts("new value is the same"):
        liquidations_peripheral.setLiquidationsCoreAddress(liquidations_core, sender=contract_owner)


def test_add_loans_core_address_wrong_sender(liquidations_peripheral, erc20, borrower):
    loans_core = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.addLoansCoreAddress(erc20, loans_core, sender=borrower)


def test_add_loans_core_address_zero_address(liquidations_peripheral, erc20, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral.addLoansCoreAddress(erc20, ZERO_ADDRESS, sender=contract_owner)


def test_remove_loans_core_address_wrong_sender(liquidations_peripheral, erc20, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.removeLoansCoreAddress(erc20, sender=borrower)


def test_remove_loans_core_address_zero_address(liquidations_peripheral, contract_owner):
    with boa.reverts("erc20TokenAddr is the zero addr"):
        liquidations_peripheral.removeLoansCoreAddress(ZERO_ADDRESS, sender=contract_owner)


def test_add_lending_pool_peripheral_address_wrong_sender(liquidations_peripheral, erc20, borrower):
    lending_pool_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.addLendingPoolPeripheralAddress(erc20, lending_pool_peripheral, sender=borrower)


def test_add_lending_pool_peripheral_address_zero_address(liquidations_peripheral, erc20, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral.addLendingPoolPeripheralAddress(erc20, ZERO_ADDRESS, sender=contract_owner)


def test_remove_lending_pool_peripheral_address_wrong_sender(liquidations_peripheral, erc20, borrower):
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.removeLendingPoolPeripheralAddress(erc20, sender=borrower)


def test_remove_lending_pool_peripheral_address_zero_address(liquidations_peripheral, contract_owner):
    with boa.reverts("erc20TokenAddr is the zero addr"):
        liquidations_peripheral.removeLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_collateral_vault_address_wrong_sender(liquidations_peripheral, borrower):
    collateral_vault_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=borrower)


def test_set_collateral_vault_address_zero_address(liquidations_peripheral, contract_owner):
    with boa.reverts("address is the zero addr"):
        liquidations_peripheral.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_max_penalty_fee(liquidations_peripheral, contract_owner):
    erc20 = boa.env.generate_address()
    max_fee = 123
    liquidations_peripheral.setMaxPenaltyFee(erc20, max_fee, sender=contract_owner)

    event = get_last_event(liquidations_peripheral, name="MaxPenaltyFeeSet")

    assert liquidations_peripheral.maxPenaltyFee(erc20) == max_fee

    assert event.erc20TokenContract == erc20
    assert event.currentValue == 0
    assert event.newValue == max_fee


def test_set_max_penalty_fee_wrong_sender(liquidations_peripheral, borrower):
    erc20 = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        liquidations_peripheral.setMaxPenaltyFee(erc20, 1, sender=borrower)


def test_set_max_penalty_fee_zero_address(liquidations_peripheral, contract_owner):
    with boa.reverts("addr is the zero addr"):
        liquidations_peripheral.setMaxPenaltyFee(ZERO_ADDRESS, 1, sender=contract_owner)
