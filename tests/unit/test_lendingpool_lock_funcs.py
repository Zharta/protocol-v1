import boa
import pytest
from datetime import datetime as dt

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
    lockPeriodEnd = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    with boa.reverts("msg.sender is not LP peripheral"):
        lending_pool_lock.setInvestorLock(investor, 10**18, lockPeriodEnd, sender=investor)


def test_set_investor_lock(lending_pool_lock, investor):
    lending_pool_peripheral = lending_pool_lock.lendingPoolPeripheral()
    lockPeriodEnd = int(dt.now().timestamp()) + LOCK_PERIOD_DURATION
    lockPeriodAmount = 10**18
    lending_pool_lock.setInvestorLock(investor, lockPeriodAmount, lockPeriodEnd, sender=lending_pool_peripheral)

    lock = lending_pool_lock.investorLocks(investor)
    assert lock[0] == lockPeriodEnd
    assert lock[1] == lockPeriodAmount
