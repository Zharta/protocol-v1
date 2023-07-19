import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module")
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc20_token(weth9_contract, contract_owner):
    with boa.env.prank(contract_owner):
        contract = weth9_contract.deploy("ERC20", "ERC20", 18, 10**20)
        boa.env.set_balance(contract.address, 10**20)
        return contract


@pytest.fixture(scope="module")
def cryptopunks(cryptopunks_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return cryptopunks_contract.deploy()


@pytest.fixture(scope="module")
def delegation_registry(delegation_registry_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return delegation_registry_contract.deploy()


@pytest.fixture(scope="module")
def collateral_vault_otc(collateral_vault_otc_contract, contract_owner, delegation_registry, cryptopunks):
    with boa.env.prank(contract_owner):
        contract = collateral_vault_otc_contract.deploy(cryptopunks, delegation_registry)
        proxy_address = contract.create_proxy()
        return collateral_vault_otc_contract.at(proxy_address)


def test_initial_state(collateral_vault_otc, delegation_registry, cryptopunks, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert collateral_vault_otc.owner() == contract_owner
    assert collateral_vault_otc.delegationRegistry() == delegation_registry.address
    assert collateral_vault_otc.cryptoPunksMarketAddress() == cryptopunks.address


def test_propose_owner_wrong_sender(collateral_vault_otc, borrower):
    with boa.reverts("msg.sender is not the owner"):
        collateral_vault_otc.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(collateral_vault_otc, contract_owner):
    with boa.reverts("address it the zero address"):
        collateral_vault_otc.proposeOwner(ZERO_ADDRESS, sender=contract_owner)


def test_propose_owner_same_owner(collateral_vault_otc, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        collateral_vault_otc.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(collateral_vault_otc, contract_owner, borrower):
    collateral_vault_otc.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(collateral_vault_otc, name="OwnerProposed")

    assert collateral_vault_otc.owner() == contract_owner
    assert collateral_vault_otc.proposedOwner() == borrower

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(collateral_vault_otc, contract_owner, borrower):
    collateral_vault_otc.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        collateral_vault_otc.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(collateral_vault_otc, contract_owner, borrower):
    collateral_vault_otc.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        collateral_vault_otc.claimOwnership(sender=contract_owner)


def test_claim_ownership(collateral_vault_otc, contract_owner, borrower):
    collateral_vault_otc.proposeOwner(borrower, sender=contract_owner)

    collateral_vault_otc.claimOwnership(sender=borrower)
    event = get_last_event(collateral_vault_otc, name="OwnershipTransferred")

    assert collateral_vault_otc.owner() == borrower
    assert collateral_vault_otc.proposedOwner() == ZERO_ADDRESS

    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_loans_address_wrong_sender(collateral_vault_otc, borrower):
    with boa.reverts():
        collateral_vault_otc.setLoansAddress(ZERO_ADDRESS, sender=borrower)


def test_set_loans_address_zero_address(collateral_vault_otc, contract_owner):
    with boa.reverts():
        collateral_vault_otc.setLoansAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_loans_address(collateral_vault_otc, contract_owner):
    loans_peripheral = boa.env.generate_address()

    collateral_vault_otc.setLoansAddress(loans_peripheral, sender=contract_owner)

    event = get_last_event(collateral_vault_otc, name="LoansPeripheralAddressSet")
    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == loans_peripheral

    assert collateral_vault_otc.loansAddress() == loans_peripheral


def test_set_liquidations_address_wrong_sender(collateral_vault_otc, borrower):
    with boa.reverts():
        collateral_vault_otc.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=borrower)


def test_set_liquidations_address_zero_address(collateral_vault_otc, contract_owner):
    with boa.reverts():
        collateral_vault_otc.setLiquidationsPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_liquidations_address(collateral_vault_otc, contract_owner):
    liquidations_peripheral = boa.env.generate_address()
    collateral_vault_otc.setLiquidationsPeripheralAddress(liquidations_peripheral, sender=contract_owner)
    event = get_last_event(collateral_vault_otc, name="LiquidationsPeripheralAddressSet")

    assert collateral_vault_otc.liquidationsPeripheralAddress() == liquidations_peripheral

    assert event.currentValue == ZERO_ADDRESS
    assert event.newValue == liquidations_peripheral


def test_transfer_collateral_from_loan_mapping_not_found(collateral_vault_otc, borrower):
    erc20 = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    with boa.reverts("mapping not found"):
        collateral_vault_otc.transferCollateralFromLoan(borrower, erc721, 0, erc20)


def test_store_collateral_mapping_not_found(collateral_vault_otc, borrower):
    erc20 = boa.env.generate_address()
    erc721 = boa.env.generate_address()
    with boa.reverts("mapping not found"):
        collateral_vault_otc.storeCollateral(borrower, erc721, 0, erc20, False)
