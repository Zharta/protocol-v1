from textwrap import dedent

import boa
import pytest
from boa.test import strategy
from hypothesis import given

from ..conftest_base import ZERO_ADDRESS, get_last_event

DEPLOYER = boa.env.generate_address()
LENDER = boa.env.generate_address()

ERC20_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

PROTOCOL_WALLET = boa.env.generate_address()
PROTOCOL_FEE = 100  # bps


@pytest.fixture(scope="module")
def lendingpool_otc(lendingpool_erc20_otc_contract):
    with boa.env.prank(DEPLOYER):
        return lendingpool_erc20_otc_contract.deploy(ERC20_ADDRESS)


@pytest.fixture(scope="module")
def lendingpool_otc_proxy(lendingpool_otc, lendingpool_erc20_otc_contract):
    with boa.env.prank(DEPLOYER):
        proxy_address = lendingpool_otc.create_proxy(PROTOCOL_WALLET, PROTOCOL_FEE, LENDER)
        return lendingpool_erc20_otc_contract.at(proxy_address)


def test_initial_state(lendingpool_otc, lendingpool_otc_proxy):
    assert lendingpool_otc.owner() == DEPLOYER
    assert lendingpool_otc.erc20TokenContract() == ERC20_ADDRESS
    assert lendingpool_otc.lender() == ZERO_ADDRESS
    assert lendingpool_otc.isPoolDeprecated() is True


def test_proxy_initial_state(lendingpool_otc_proxy):
    assert lendingpool_otc_proxy.owner() == DEPLOYER
    assert lendingpool_otc_proxy.erc20TokenContract() == ERC20_ADDRESS
    assert lendingpool_otc_proxy.lender() == LENDER
    assert lendingpool_otc_proxy.protocolWallet() == PROTOCOL_WALLET
    assert lendingpool_otc_proxy.protocolFeesShare() == PROTOCOL_FEE
    assert lendingpool_otc_proxy.isPoolActive() is True
    assert lendingpool_otc_proxy.isPoolDeprecated() is False


def test_initialize(lendingpool_otc, lendingpool_otc_proxy):
    with boa.reverts("already initialized"):
        lendingpool_otc.initialize(DEPLOYER, LENDER, PROTOCOL_WALLET, PROTOCOL_FEE, sender=DEPLOYER)

    with boa.reverts("already initialized"):
        lendingpool_otc_proxy.initialize(DEPLOYER, LENDER, PROTOCOL_WALLET, PROTOCOL_FEE, sender=DEPLOYER)


@pytest.mark.parametrize("contract_fixture", ["lendingpool_otc", "lendingpool_otc_proxy"])
def test_propose_owner(contract_fixture, request):
    account1 = boa.env.generate_address()
    account2 = boa.env.generate_address()

    contract = request.getfixturevalue(contract_fixture)
    with boa.reverts():
        contract.proposeOwner(account1, sender=account2)

    contract.proposeOwner(account1, sender=DEPLOYER)
    event = get_last_event(contract, name="OwnerProposed")

    assert contract.owner() == DEPLOYER
    assert contract.proposedOwner() == account1

    assert event.owner == DEPLOYER
    assert event.proposedOwner == account1


@pytest.mark.parametrize("contract_fixture", ["lendingpool_otc", "lendingpool_otc_proxy"])
def test_claim_ownership(contract_fixture, request):
    account1 = boa.env.generate_address()
    account2 = boa.env.generate_address()

    contract = request.getfixturevalue(contract_fixture)
    with boa.reverts():
        contract.claimOwnership(sender=account1)

    contract.proposeOwner(account2, sender=DEPLOYER)
    contract.claimOwnership(sender=account2)
    event = get_last_event(contract, name="OwnershipTransferred")

    assert contract.owner() == account2
    assert contract.proposedOwner() == ZERO_ADDRESS

    assert event.owner == DEPLOYER
    assert event.proposedOwner == account2


def test_deprecate(lendingpool_otc_proxy):
    account1 = boa.env.generate_address()

    with boa.reverts():
        lendingpool_otc_proxy.deprecate(sender=account1)

    assert not lendingpool_otc_proxy.isPoolDeprecated()

    lendingpool_otc_proxy.deprecate(sender=DEPLOYER)
    event = get_last_event(lendingpool_otc_proxy, name="ContractDeprecated")

    assert lendingpool_otc_proxy.isPoolDeprecated()
    assert not lendingpool_otc_proxy.isPoolActive()

    assert event.erc20TokenContract == ERC20_ADDRESS


def test_deprecate_blockers(lendingpool_otc, lendingpool_otc_proxy):
    account1 = boa.env.generate_address()
    account2 = boa.env.generate_address()
    boa.env.set_balance(account1, 10)

    inject_code_allowed = """
        @view
        @internal
        def _fundsAreAllowed(_owner: address, _spender: address, _amount: uint256) -> bool:
            return True
    """

    inject_code_wrap = """
        @internal
        def _wrap(_amount: uint256):
            pass
    """

    lendingpool_otc.inject_function(dedent(inject_code_allowed), force=True)
    lendingpool_otc.inject_function(dedent(inject_code_wrap), force=True)

    with boa.reverts():
        lendingpool_otc.deposit(1, sender=account1)

    with boa.reverts():
        lendingpool_otc.depositEth(value=1, sender=account1)

    with boa.reverts():
        lendingpool_otc.sendFunds(account2, 1, sender=account1)

    lendingpool_otc_proxy.deprecate(sender=lendingpool_otc_proxy.owner())

    with boa.reverts():
        lendingpool_otc_proxy.deposit(1, sender=account1)

    with boa.reverts():
        lendingpool_otc_proxy.depositEth(value=1, sender=account1)

    with boa.reverts():
        lendingpool_otc_proxy.sendFunds(account2, 1, sender=account1)


def test_change_status(lendingpool_otc_proxy):
    account1 = boa.env.generate_address()

    with boa.reverts():
        lendingpool_otc_proxy.changePoolStatus(False, sender=account1)
    assert lendingpool_otc_proxy.isPoolActive()

    lendingpool_otc_proxy.changePoolStatus(False, sender=DEPLOYER)
    event = get_last_event(lendingpool_otc_proxy, name="ContractStatusChanged")

    assert not lendingpool_otc_proxy.isPoolActive()
    assert event.erc20TokenContract == ERC20_ADDRESS
    assert event.value is False

    lendingpool_otc_proxy.changePoolStatus(True, sender=DEPLOYER)
    event = get_last_event(lendingpool_otc_proxy, name="ContractStatusChanged")

    assert lendingpool_otc_proxy.isPoolActive()
    assert event.erc20TokenContract == ERC20_ADDRESS
    assert event.value is True


def test_loans_peripheral_address(lendingpool_otc_proxy):
    account1 = boa.env.generate_address()
    lp = boa.env.generate_address()

    with boa.reverts():
        lendingpool_otc_proxy.setLoansPeripheralAddress(lp, sender=account1)
    assert lendingpool_otc_proxy.loansContract() == ZERO_ADDRESS

    lendingpool_otc_proxy.setLoansPeripheralAddress(lp, sender=lendingpool_otc_proxy.owner())
    assert lendingpool_otc_proxy.loansContract() == lp


def test_liquidations_peripheral_address(lendingpool_otc_proxy):
    account1 = boa.env.generate_address()
    lp = boa.env.generate_address()

    with boa.reverts():
        lendingpool_otc_proxy.setLiquidationsPeripheralAddress(lp, sender=account1)
    assert lendingpool_otc_proxy.liquidationsPeripheralContract() == ZERO_ADDRESS

    lendingpool_otc_proxy.setLiquidationsPeripheralAddress(lp, sender=lendingpool_otc_proxy.owner())
    assert lendingpool_otc_proxy.liquidationsPeripheralContract() == lp


def test_change_protocol_fees_fail(lendingpool_otc_proxy):
    account1 = boa.env.generate_address()

    with boa.reverts():
        lendingpool_otc_proxy.changeProtocolFeesShare(500, sender=account1)

    assert lendingpool_otc_proxy.protocolFeesShare() == PROTOCOL_FEE

    with boa.reverts():
        lendingpool_otc_proxy.changeProtocolFeesShare(10001, sender=DEPLOYER)

    assert lendingpool_otc_proxy.protocolFeesShare() == PROTOCOL_FEE


@given(value=strategy("uint256", max_value=10000))
def test_change_protocol_fees(value, lendingpool_otc_proxy):
    lendingpool_otc_proxy.changeProtocolFeesShare(value, sender=DEPLOYER)
    event = get_last_event(lendingpool_otc_proxy, name="ProtocolFeesShareChanged")
    assert lendingpool_otc_proxy.protocolFeesShare() == value
    assert event.newValue == value
    assert event.erc20TokenContract == ERC20_ADDRESS
