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
def liquidations_otc_impl(liquidations_otc_contract, owner):
    with boa.env.prank(owner):
        return liquidations_otc_contract.deploy()


@pytest.fixture(scope="module")
def liquidations_otc(liquidations_otc_contract, liquidations_otc_impl, weth, owner):
    with boa.env.prank(owner):
        loans = boa.env.generate_address("loans")
        lending_pool = boa.env.generate_address("loans")
        collateral_vault = boa.env.generate_address("loans")
        proxy_address = liquidations_otc_impl.create_proxy(GRACE_PERIOD_DURATION, loans, lending_pool, collateral_vault)
        return liquidations_otc_contract.at(proxy_address)


def test_initial_state(liquidations_otc, owner):
    assert liquidations_otc.owner() == owner
    assert liquidations_otc.gracePeriodDuration() == GRACE_PERIOD_DURATION


def test_propose_owner(liquidations_otc, owner):
    random_account = boa.env.generate_address()

    with boa.reverts():
        liquidations_otc.proposeOwner(random_account, sender=random_account)

    with boa.reverts():
        liquidations_otc.proposeOwner(ZERO_ADDRESS, sender=owner)

    liquidations_otc.proposeOwner(random_account, sender=owner)
    event = get_last_event(liquidations_otc, name="OwnerProposed")
    assert event.owner == owner
    assert event.proposedOwner == random_account

    assert liquidations_otc.owner() == owner
    assert liquidations_otc.proposedOwner() == random_account


def test_claim_ownership(liquidations_otc, owner):
    random_account = boa.env.generate_address()

    with boa.reverts():
        liquidations_otc.claimOwnership(sender=owner)

    liquidations_otc.proposeOwner(random_account, sender=owner)
    liquidations_otc.claimOwnership(sender=random_account)

    event = get_last_event(liquidations_otc, name="OwnershipTransferred")
    assert event.owner == owner
    assert event.proposedOwner == random_account

    assert liquidations_otc.owner() == random_account
    assert liquidations_otc.proposedOwner() == ZERO_ADDRESS


def test_set_grace_period_duration(liquidations_otc, owner):
    duration = 100

    # account not owner
    with boa.reverts():
        liquidations_otc.setGracePeriodDuration(duration, sender=boa.env.generate_address())

    # duration is 0
    with boa.reverts():
        liquidations_otc.setGracePeriodDuration(0, sender=owner)

    liquidations_otc.setGracePeriodDuration(duration, sender=owner)
    assert liquidations_otc.gracePeriodDuration() == duration
