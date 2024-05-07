from datetime import datetime as dt

import boa
import pytest

LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def lending_pool_lock(lendingpool_lock_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return lendingpool_lock_contract.deploy(boa.env.generate_address())


def test_set_investor_lock_wrong_sender(lending_pool_lock, investor):
    loack_period_end = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_lock.setInvestorLock(investor, 10**18, loack_period_end, sender=investor)


def test_set_investor_lock(lending_pool_lock, investor):
    lending_pool_peripheral = lending_pool_lock.lendingPoolPeripheral()
    loack_period_end = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    lock_period_amount = 10**18
    lending_pool_lock.setInvestorLock(investor, lock_period_amount, loack_period_end, sender=lending_pool_peripheral)

    lock = lending_pool_lock.investorLocks(investor)
    assert lock[0] == loack_period_end
    assert lock[1] == lock_period_amount
