import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def loans_core(loans_core_contract, path_to_erc20_mock, contract_owner):
    with boa.env.prank(contract_owner):
        contract = loans_core_contract.deploy()
        contract.setLoansPeripheral(path_to_erc20_mock.deploy())
        return contract


def test_initial_state(loans_core, contract_owner):
    assert loans_core.owner() == contract_owner


def test_set_loans_peripheral(loans_core, contract_owner, path_to_erc20_mock):
    old_loans_peripheral = loans_core.loansPeripheral()
    loans_peripheral = path_to_erc20_mock.deploy()

    loans_core.setLoansPeripheral(loans_peripheral, sender=contract_owner)
    event = get_last_event(loans_core, name="LoansPeripheralAddressSet")

    assert loans_core.loansPeripheral() == loans_peripheral.address
    assert event.currentValue == old_loans_peripheral
    assert event.newValue == loans_peripheral.address


def test_propose_owner_wrong_sender(loans_core, borrower, contract_owner):
    with boa.reverts("msg.sender is not the owner"):
        loans_core.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(loans_core, contract_owner):
    with boa.reverts("_address it the zero address"):
        loans_core.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(loans_core, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        loans_core.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(loans_core, contract_owner, borrower):
    loans_core.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(loans_core, name="OwnerProposed")

    assert loans_core.proposedOwner() == borrower
    assert loans_core.owner() == contract_owner
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(loans_core, contract_owner, borrower):
    loans_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        loans_core.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(loans_core, contract_owner, borrower):
    loans_core.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        loans_core.claimOwnership(sender=contract_owner)


def test_claim_ownership(loans_core, contract_owner, borrower):
    loans_core.proposeOwner(borrower, sender=contract_owner)

    loans_core.claimOwnership(sender=borrower)
    event = get_last_event(loans_core, name="OwnershipTransferred")

    assert loans_core.owner() == borrower
    assert loans_core.proposedOwner() == ZERO_ADDRESS
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_loans_peripheral_wrong_sender(loans_core, borrower):
    loans_peripheral = boa.env.generate_address()
    with boa.reverts("msg.sender is not the owner"):
        loans_core.setLoansPeripheral(loans_peripheral, sender=borrower)


def test_set_loans_peripheral_zero_address(loans_core, contract_owner):
    with boa.reverts("_address is the zero address"):
        loans_core.setLoansPeripheral(ZERO_ADDRESS, sender=contract_owner)


def test_set_loans_peripheral_same_address(loans_core, contract_owner):
    loans_peripheral = loans_core.loansPeripheral()
    with boa.reverts("new loans addr is the same"):
        loans_core.setLoansPeripheral(loans_peripheral, sender=contract_owner)
