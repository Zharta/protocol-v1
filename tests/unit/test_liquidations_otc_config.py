import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event

GRACE_PERIOD_DURATION = 86400


@pytest.fixture(scope="module", autouse=True)
def owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def weth():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def liquidations_otc(liquidations_otc_contract, weth, owner):
    with boa.env.prank(owner):
        return liquidations_otc_contract.deploy(GRACE_PERIOD_DURATION, weth)


def test_initial_state(liquidations_otc, owner):
    assert liquidations_otc.owner() == owner
    assert liquidations_otc.gracePeriodDuration() == GRACE_PERIOD_DURATION


def test_propose_owner(liquidations_otc, owner):
    random_account = boa.env.generate_address()

    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.proposeOwner(random_account, sender=random_account)

    with boa.reverts(reason="address it the zero address"):
        liquidations_otc.proposeOwner(ZERO_ADDRESS, sender=owner)

    liquidations_otc.proposeOwner(random_account, sender=owner)
    event = get_last_event(liquidations_otc, name="OwnerProposed")
    assert event.owner == owner
    assert event.proposedOwner == random_account

    assert liquidations_otc.owner() == owner
    assert liquidations_otc.proposedOwner() == random_account


def test_claim_ownership(liquidations_otc, owner):
    random_account = boa.env.generate_address()

    with boa.reverts(reason="msg.sender is not the proposed"):
        liquidations_otc.claimOwnership(sender=owner)

    liquidations_otc.proposeOwner(random_account, sender=owner)
    liquidations_otc.claimOwnership(sender=random_account)

    event = get_last_event(liquidations_otc, name="OwnershipTransferred")
    assert event.owner == owner
    assert event.proposedOwner == random_account

    assert liquidations_otc.owner() == random_account
    assert liquidations_otc.proposedOwner() == ZERO_ADDRESS


def test_loans_peripheral_address(liquidations_otc, owner):
    erc20 = boa.env.generate_address()
    loans_core = boa.env.generate_address()

    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.addLoansCoreAddress(erc20, loans_core, sender=boa.env.generate_address())

    with boa.reverts(reason="address is the zero addr"):
        liquidations_otc.addLoansCoreAddress(erc20, ZERO_ADDRESS, sender=owner)

    with boa.reverts(reason="erc20TokenAddr is the zero addr"):
        liquidations_otc.addLoansCoreAddress(ZERO_ADDRESS, loans_core, sender=owner)

    liquidations_otc.addLoansCoreAddress(erc20, loans_core, sender=owner)
    assert liquidations_otc.loansCoreAddresses(erc20) == loans_core


def test_remove_loans_core_address(liquidations_otc, owner):
    erc20 = boa.env.generate_address()
    loans_core = boa.env.generate_address()

    # account not owner
    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.removeLoansCoreAddress(erc20, sender=boa.env.generate_address())

    # erc20TokenAddr is the zero addr
    with boa.reverts(reason="erc20TokenAddr is the zero addr"):
        liquidations_otc.removeLoansCoreAddress(ZERO_ADDRESS, sender=owner)

    # address not found
    with boa.reverts(reason="address not found"):
        liquidations_otc.removeLoansCoreAddress(erc20, sender=owner)

    liquidations_otc.addLoansCoreAddress(erc20, loans_core, sender=owner)
    liquidations_otc.removeLoansCoreAddress(erc20, sender=owner)
    assert liquidations_otc.loansCoreAddresses(erc20) == ZERO_ADDRESS


def test_add_lending_pool_peripheral_address(liquidations_otc, owner):
    erc20 = boa.env.generate_address()
    peripheral_address = boa.env.generate_address()

    # account not owner
    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.addLendingPoolPeripheralAddress(erc20, peripheral_address, sender=boa.env.generate_address())

    # address is the zero addr
    with boa.reverts(reason="address is the zero addr"):
        liquidations_otc.addLendingPoolPeripheralAddress(erc20, ZERO_ADDRESS, sender=owner)

    # erc20TokenAddr is the zero addr
    with boa.reverts(reason="erc20TokenAddr is the zero addr"):
        liquidations_otc.addLendingPoolPeripheralAddress(ZERO_ADDRESS, peripheral_address, sender=owner)

    liquidations_otc.addLendingPoolPeripheralAddress(erc20, peripheral_address, sender=owner)
    assert liquidations_otc.lendingPoolPeripheralAddresses(erc20) == peripheral_address


def test_remove_lending_pool_peripheral_address(liquidations_otc, owner):
    erc20 = boa.env.generate_address()
    peripheral_address = boa.env.generate_address()

    # account not owner
    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.removeLendingPoolPeripheralAddress(erc20, sender=boa.env.generate_address())

    # erc20TokenAddr is the zero addr
    with boa.reverts(reason="erc20TokenAddr is the zero addr"):
        liquidations_otc.removeLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=owner)

    # address not found
    with boa.reverts(reason="address not found"):
        liquidations_otc.removeLendingPoolPeripheralAddress(erc20, sender=owner)

    liquidations_otc.addLendingPoolPeripheralAddress(erc20, peripheral_address, sender=owner)
    liquidations_otc.removeLendingPoolPeripheralAddress(erc20, sender=owner)
    assert liquidations_otc.lendingPoolPeripheralAddresses(erc20) == ZERO_ADDRESS


def test_set_collateral_vault_peripheral_address(liquidations_otc, owner):
    peripheral_address = boa.env.generate_address()

    # account not owner
    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.setCollateralVaultPeripheralAddress(peripheral_address, sender=boa.env.generate_address())

    # address is the zero addr
    with boa.reverts(reason="address is the zero addr"):
        liquidations_otc.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=owner)

    liquidations_otc.setCollateralVaultPeripheralAddress(peripheral_address, sender=owner)
    assert liquidations_otc.collateralVaultPeripheralAddress() == peripheral_address


def test_set_grace_period_duration(liquidations_otc, owner):
    duration = 100

    # account not owner
    with boa.reverts(reason="msg.sender is not the owner"):
        liquidations_otc.setGracePeriodDuration(duration, sender=boa.env.generate_address())

    # duration is 0
    with boa.reverts(reason="duration is 0"):
        liquidations_otc.setGracePeriodDuration(0, sender=owner)

    liquidations_otc.setGracePeriodDuration(duration, sender=owner)
    assert liquidations_otc.gracePeriodDuration() == duration
