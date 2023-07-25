import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event

INTEREST_ACCRUAL_PERIOD = 24 * 60 * 60

@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def lending_pool(path_to_erc20_mock):
    return path_to_erc20_mock.deploy()


@pytest.fixture(scope="module")
def collateral_vault(empty_contract):
    return empty_contract.deploy()


@pytest.fixture(scope="module")
def genesis(empty_contract):
    return empty_contract.deploy()


@pytest.fixture(scope="module")
def loans_otc_impl(loans_otc_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return loans_otc_contract.deploy()


@pytest.fixture(scope="module")
def loans_otc(loans_otc_contract, loans_otc_impl, contract_owner, lending_pool, collateral_vault, genesis):
    with boa.env.prank(contract_owner):
        proxy = loans_otc_impl.create_proxy(INTEREST_ACCRUAL_PERIOD, lending_pool, collateral_vault, genesis, True)
        return loans_otc_contract.at(proxy)


def test_initial_state_impl(loans_otc_impl, contract_owner):
    assert loans_otc_impl.owner() == contract_owner
    assert loans_otc_impl.isDeprecated()
    assert not loans_otc_impl.isAcceptingLoans()


def test_initial_state(loans_otc, contract_owner, lending_pool, collateral_vault, genesis):
    assert loans_otc.owner() == contract_owner
    assert loans_otc.admin() == contract_owner
    assert loans_otc.interestAccrualPeriod() == INTEREST_ACCRUAL_PERIOD
    assert loans_otc.lendingPoolContract() == lending_pool.address
    assert loans_otc.collateralVaultContract() == collateral_vault.address
    assert loans_otc.genesisContract() == genesis.address
    assert not loans_otc.isDeprecated()
    assert loans_otc.isAcceptingLoans()


def test_propose_owner_wrong_sender(loans_otc, borrower, contract_owner):
    with boa.reverts("msg.sender is not the owner"):
        loans_otc.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(loans_otc, contract_owner):
    with boa.reverts("_address it the zero address"):
        loans_otc.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(loans_otc, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        loans_otc.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(loans_otc, contract_owner, borrower):
    loans_otc.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(loans_otc, name="OwnerProposed")

    assert loans_otc.proposedOwner() == borrower
    assert loans_otc.owner() == contract_owner
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(loans_otc, contract_owner, borrower):
    loans_otc.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        loans_otc.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(loans_otc, contract_owner, borrower):
    loans_otc.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        loans_otc.claimOwnership(sender=contract_owner)


def test_claim_ownership(loans_otc, contract_owner, borrower):
    loans_otc.proposeOwner(borrower, sender=contract_owner)

    loans_otc.claimOwnership(sender=borrower)
    event = get_last_event(loans_otc, name="OwnershipTransferred")

    assert loans_otc.owner() == borrower
    assert loans_otc.proposedOwner() == ZERO_ADDRESS
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_lending_pool(loans_otc, contract_owner, path_to_erc20_mock, borrower):
    old_lending_pool = loans_otc.lendingPoolContract()
    lending_pool = path_to_erc20_mock.deploy()

    # msg.sender is not the owner
    with boa.reverts():
        loans_otc.setLendingPoolPeripheralAddress(lending_pool, sender=borrower)

    # address is the zero address
    with boa.reverts():
        loans_otc.setLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)

    loans_otc.setLendingPoolPeripheralAddress(lending_pool, sender=contract_owner)

    event = get_last_event(loans_otc, name="LendingPoolPeripheralAddressSet")
    assert event.currentValue == old_lending_pool
    assert event.newValue == lending_pool.address

    assert loans_otc.lendingPoolContract() == lending_pool.address


def test_set_collateral_vault(loans_otc, contract_owner, path_to_erc20_mock, borrower):
    old_collateral_vault = loans_otc.collateralVaultContract()
    collateral_vault = path_to_erc20_mock.deploy()

    # msg.sender is not the owner
    with boa.reverts():
        loans_otc.setCollateralVaultPeripheralAddress(collateral_vault, sender=borrower)

    # address is the zero address
    with boa.reverts():
        loans_otc.setCollateralVaultPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)

    loans_otc.setCollateralVaultPeripheralAddress(collateral_vault, sender=contract_owner)

    event = get_last_event(loans_otc, name="CollateralVaultPeripheralAddressSet")
    assert event.currentValue == old_collateral_vault
    assert event.newValue == collateral_vault.address

    assert loans_otc.collateralVaultContract() == collateral_vault.address


def test_set_liquidations(loans_otc, contract_owner, path_to_erc20_mock, borrower):
    old_liquidations = loans_otc.liquidationsContract()
    liquidations = path_to_erc20_mock.deploy()

    # msg.sender is not the owner
    with boa.reverts():
        loans_otc.setLiquidationsPeripheralAddress(liquidations, sender=borrower)

    # address is the zero address
    with boa.reverts():
        loans_otc.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)

    loans_otc.setLiquidationsPeripheralAddress(liquidations, sender=contract_owner)

    event = get_last_event(loans_otc, name="LiquidationsPeripheralAddressSet")
    assert event.currentValue == old_liquidations
    assert event.newValue == liquidations.address

    assert loans_otc.liquidationsContract() == liquidations.address


def test_change_admin(loans_otc, contract_owner):
    admin = boa.env.generate_address("admin")
    old_admin = loans_otc.admin()

    # msg.sender is not the owner
    with boa.reverts():
        loans_otc.changeAdmin(admin, sender=admin)

    loans_otc.changeAdmin(admin, sender=contract_owner)

    event = get_last_event(loans_otc, name="AdminTransferred")
    assert event.currentValue == old_admin
    assert event.newValue == admin

    assert loans_otc.admin() == admin


